from datetime import timedelta
from typing import List

from numpy.random import poisson, choice
import pandas as pd
from station import Station
from trip import Trip


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

    def sim(self):
        """

        :return:
        """
        self.curr_tick += 1
        self.curr_time += timedelta(hours=1 / self.tph)
        if self.curr_tick % (24*self.tph) == 0:
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
                        self.stations_dict[trip.end_station])  # go to closest station to proposed end
                    if new_destination in self.stations_dict[trip.end_station].neighbors_dist:
                        new_trip = Trip(start_station=trip.end_station,
                                        end_station=new_destination,
                                        start_time=self.curr_time,
                                        trip_time=self.stations_dict[trip.end_station].neighbors_dist[new_destination])
                        transit.append(new_trip)
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
                trip = Trip(start_station=station.name,
                            end_station=destination,
                            start_time=self.curr_time,
                            trip_time=station.neighbors_dist[destination])
                if not station.get_bike(trip):
                    self.failures += 1
                    # print('Failure to depart from ', station_name)
                    # This all needs to be fixed to account for people that can't depart

                    new_departure_pt = self.get_new_station(station)
                    # print('Failure rerouted to: ', new_departure_pt)
                    if new_departure_pt and not self.stations_dict[new_departure_pt].empty:
                        # print(new_departure_pt, ' has a bike to use')
                        trip.end_station = new_departure_pt
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

    def mean_sq_error(self, other_stations: {str: Station}):
        error = 0
        for station in self.stations_dict:
            error += (self.stations_dict[station].curr_bikes - other_stations[station].curr_bikes) ** 2
        return error/len(self.stations_dict)
