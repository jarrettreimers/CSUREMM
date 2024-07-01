from datetime import timedelta
from typing import List

from math import floor
from numpy.random import poisson, choice
import pandas as pd
import numpy as np
from station import Station
from trip import Trip


def get_dist(start_station: Station, end_station: Station) -> timedelta:
    if end_station in start_station.neighbors_dist:
        return start_station.neighbors_dist[end_station]
    minutes = np.sqrt(
        (start_station.lat - end_station.lat) ** 2 + (start_station.lon - end_station.lon) ** 2) * 428 + 5
    return timedelta(minutes=minutes)


class Model:
    def __init__(self,
                 station_names: [],
                 stations_dict: {str: Station},
                 in_transit: List[Trip],
                 tph: int
                 ):
        """
        :param station_names:
        :param stations_dict
        :param in_transit:
        :param tph:
        """
        self.station_names = station_names
        self.stations_dict = stations_dict
        self.in_transit = in_transit
        self.tph = tph
        self.curr_tick = 0
        self.curr_time = timedelta(hours=0)
        self.failures = 0
        self.total_trips = 0
        self.critical_failures = 0
        self.clusters = []

    def sim(self):
        """

        :return:
        """
        self.curr_tick += 1
        self.curr_time += timedelta(hours=1 / self.tph)
        if self.curr_tick % (24 * self.tph) == 0:
            self.curr_tick = 0
        transit = self.sim_trips()
        transit += self.sim_stations()
        self.in_transit = transit

    def sim_trips(self) -> List[Trip]:
        transit = []
        for trip in self.in_transit:
            # updates the time for each trip
            if trip.update(timedelta(hours=1 / self.tph)):
                # park the bike
                if not self.stations_dict[trip.end_station].return_bike(trip):  # if there is no room...
                    # print('Failure to dock') # TODO handle dock failure
                    self.failures += 1
                    new_destination = self.get_new_station(
                        self.stations_dict[trip.end_station])  # go to nearest station to proposed end
                    if new_destination:
                        distance = get_dist(self.stations_dict[trip.end_station], self.stations_dict[new_destination])
                        new_trip = Trip(start_station=trip.end_station,
                                        end_station=new_destination,
                                        start_time=self.curr_time,
                                        trip_time=distance)
                        transit.append(new_trip)
                    else:
                        self.critical_failures += 1
                else:
                    self.total_trips += 1
            else:
                transit.append(trip)
        return transit

    def sim_stations(self):
        transit = []
        for station in self.stations_dict.values():
            departures = poisson(station.rate[self.curr_tick])
            destinations = choice(station.neighbors_names, departures, p=station.transition[self.curr_tick])
            for destination in destinations:
                if destination not in self.stations_dict:
                    destination = self.get_new_station(station)
                trip = Trip(start_station=station.name,
                            end_station=destination,
                            start_time=self.curr_time,
                            trip_time=get_dist(station, self.stations_dict[destination]))
                if not station.get_bike(trip):
                    self.failures += 1
                    # print('Failure to depart from ', station_name)
                    # This all needs to be fixed to account for people that can't depart

                    new_departure_pt = self.get_new_station(station)
                    # print('Failure rerouted to: ', new_departure_pt)
                    if new_departure_pt and not self.stations_dict[new_departure_pt].empty:
                        # print(new_departure_pt, ' has a bike to use')
                        trip.start_station = new_departure_pt
                        self.stations_dict[new_departure_pt].get_bike(trip)
                        transit.append(trip)
                else:
                    transit.append(trip)
            station.update()
        return transit

    def get_new_station(self, station: Station) -> str:
        nearest_neighbors = station.nearest_neighbors
        for neighbor in nearest_neighbors[:5]:
            if neighbor in self.stations_dict and not self.stations_dict[neighbor].empty:
                return neighbor
        return ''

    def change_time(self, time: timedelta):
        self.curr_time = time
        self.curr_tick = int((time.total_seconds() * self.tph) / 3600)

    def init_state(self, path: str, time=None):
        if time:
            self.change_time(time)
        df = pd.read_csv(path)
        for station in self.stations_dict:
            self.stations_dict[station].curr_bikes = df.loc[df['name'] == station, 'num_bikes_available'].values[0]

    def mean_sq_error(self, stations_dict=None, other_stations=None, path=None):
        if other_stations is None and path is None:
            print("No comparison stations provided")
            return
        if other_stations is None:
            other_stations = get_state(path)
        if stations_dict is None:
            stations_dict = self.stations_dict
        error = 0
        for station in stations_dict:
            error += (stations_dict[station].curr_bikes - other_stations[station].curr_bikes) ** 2
        return error / len(stations_dict)

    def remove_station(self, station_name: str):
        self.stations_dict.pop(station_name)
        for station in self.stations_dict:
            self.stations_dict[station].remove_neighbor(station_name)

    def truncate_transitions(self):
        done = 0
        total = len(self.stations_dict)
        for station in self.stations_dict.values():
            station.truncate_transition()
            done += 1
            if done % 100 == 0:
                print(f'{done} of {total} done')
        print('Stations truncated')

    def refine_by_3(self):
        done = 0
        total = len(self.stations_dict)
        for station in self.stations_dict.values():
            station.refine_by_3()
            done += 1
            if done % 100 == 0:
                print(f'{done} of {total} done')
        print('Stations refined')

    def cluster_stations(self, square_length: float):
        lat_min = np.inf
        lat_max = -np.inf
        lon_min = np.inf
        lon_max = -np.inf
        for station in self.stations_dict.values():
            if station.lat < lat_min:
                lat_min = station.lat
            if station.lat > lat_max:
                lat_max = station.lat
            if station.lon < lon_min:
                lon_min = station.lon
            if station.lon > lon_max:
                lon_max = station.lon
        vertical_squares = int((lat_max - lat_min) / square_length) + 1
        horizontal_squares = int((lon_max - lon_min) / square_length) + 1
        squares = horizontal_squares * vertical_squares
        print(
            f'{horizontal_squares} horizontal squares and {vertical_squares} vertical squares. Total squares: {squares}')
        self.clusters = [[] for square in range(squares)]
        for station in self.stations_dict.values():
            x = floor((station.lon - lon_min) / square_length)
            y = -floor((station.lat - lat_min) / square_length) - 1
            self.clusters[x + y * horizontal_squares].append(station.name)

        return horizontal_squares, vertical_squares, self.clusters

    def get_num_bikes_in_clusters(self):
        bike_cluster = []
        for cluster in self.clusters:
            num_bikes = 0
            for station in cluster:
                num_bikes += self.stations_dict[station].curr_bikes
            bike_cluster.append(num_bikes)
        return bike_cluster

    def get_num_open_docks_in_clusters(self):
        dock_cluster = []
        for cluster in self.clusters:
            num_docks = 0
            for station in self.clusters[cluster]:
                num_docks += self.stations_dict[station].max_docks - self.stations_dict[station].curr_bikes
            dock_cluster.append(num_docks)
        return dock_cluster


def get_state(path: str) -> {str: Station}:
    df = pd.read_csv(path)
    stations_dict = {}
    for i in range(len(df)):
        stations_dict[df.loc[i, 'name']] = (
            Station(name=df.loc[i, 'name'],
                    lat=df.loc[i, 'lat'],
                    lon=df.loc[i, 'lon'],
                    max_docks=df.loc[i, 'capacity'],
                    curr_bikes=df.loc[i, 'num_bikes_available'],
                    rate=[],
                    transition=[],
                    id=0,
                    neighbors_dist={},
                    neighbors_names=[]))
    return stations_dict
