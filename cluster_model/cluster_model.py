import random
from datetime import timedelta
from typing import List

import matplotlib.pyplot as plt
import seaborn as sns
from math import floor
from numpy.random import poisson, choice
import pandas as pd
import numpy as np
from cluster import StationCluster
from trip import Trip


class ClusterModel:
    def __init__(self,
                 station_data: dict[str: dict[str: float]],
                 in_transit: List[Trip],
                 tph: int
                 ):
        self.cluster_dict = {}  # {cluster_name (int) : StationCluster}
        self.in_transit = in_transit  # List of Trip objects
        self.tph = tph  # Ticks per hour (int) must divide 60
        self.curr_tick = 0  # Current tick in the day
        self.curr_time = timedelta(hours=0)  # Current time in the day
        self.failures = 0  # Number of failed trips (includes rerouting)
        self.total_trips = 0  # Total number of trips
        self.critical_failures = 0  # Number of trips that could not be rerouted
        self.clusters = []  # List of lists of station names
        self.clusters_lat_lon = []  # List of lists of lat/lon
        self.station_data = station_data
        # {station_name (str) :
        # {lat (float), lon (float), max_docks (int), curr_bikes (int), rate (dict{int: int}),
        # transition (dict{int: dict{str: float}})}
        self.station_clusters = {}  # {station_name (str) : cluster_name (int)}
        self.horizontal_squares = 0  # Number of horizontal squares
        self.vertical_squares = 0  # Number of vertical squares
        self.square_length = 0  # Length of each square in lat/lon

    def sim(self):
        self.curr_tick += 1
        self.curr_time += timedelta(hours=1 / self.tph)
        if self.curr_tick % (24 * self.tph) == 0:
            self.curr_tick = 0
        transit = self.sim_trips()
        transit += self.sim_clusters()
        self.in_transit = transit

    def sim_trips(self) -> List[Trip]:
        transit = []
        for trip in self.in_transit:
            # updates the time for each trip
            if trip.update(timedelta(hours=1 / self.tph)):
                # park the bike
                end_cluster = trip.end_cluster  # int reference to cluster
                if not self.cluster_dict[end_cluster].return_bike(trip):  # if there is no room...
                    # print('Failure to dock')
                    self.failures += 1
                    new_destination = self.get_new_cluster(cluster=end_cluster, method='arrival')
                    if new_destination:
                        distance = self.get_dist(end_cluster, self.cluster_dict[new_destination])
                        new_trip = Trip(start_cluster=trip.end_cluster,
                                        end_cluster=new_destination,
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

    def sim_clusters(self):
        transit = []
        for cluster in self.cluster_dict.values():
            departures = poisson(cluster.rate[self.curr_tick])
            transition_values = np.array(list(cluster.transition[self.curr_tick].values()))
            transition_keys = np.array(list(cluster.transition[self.curr_tick].keys()))
            try:
                destinations = choice(transition_keys, departures, p=transition_values)
            except ValueError:
                print('Error in choice', cluster.name, departures, sum(transition_values), len(transition_keys))
                destinations = []
            for destination in destinations:
                if destination not in self.cluster_dict:
                    print(destination, 'Destination not in cluster_dict')
                    continue
                if self.cluster_dict[destination].full:
                    self.failures += 1
                    # print('Failure to arrive at ', station_name)
                    destination = self.get_new_cluster(cluster=destination, method='departure')
                if not destination:
                    self.critical_failures += 1
                    continue
                trip = Trip(start_cluster=cluster.name,
                            end_cluster=destination,
                            start_time=self.curr_time,
                            trip_time=self.get_dist(destination, self.cluster_dict[destination]))
                if not cluster.get_bike(trip):
                    self.failures += 1
                    # print('Failure to depart from ', station_name)
                    new_departure_pt = self.get_new_cluster(cluster.name)
                    # print('Failure rerouted to: ', new_departure_pt)
                    if new_departure_pt and self.cluster_dict[new_departure_pt].get_bike(trip):
                        # print(new_departure_pt, ' has a bike to use')
                        trip.start_station = new_departure_pt
                        transit.append(trip)
                    else:
                        # print('No bikes available at ', new_departure_pt)
                        self.critical_failures += 1
                else:
                    transit.append(trip)
        return transit

    def get_dist(self, start_cluster: int, end_cluster: int) -> timedelta:
        start_cluster = self.cluster_dict[start_cluster]
        if end_cluster in start_cluster.neighbors_dist:
            return start_cluster.neighbors_dist[end_cluster]
        # minutes = np.sqrt(
        #     (start_cluster.lat - end_cluster.lat) ** 2 + (start_cluster.lon - end_cluster.lon) ** 2) * 428 + 5
        minutes = 12
        return timedelta(minutes=minutes)

    def get_new_cluster(self, cluster: int, method='arrival'):
        nearest_neighbors = self.cluster_dict[cluster].nearest_neighbors
        random_range = [i for i in range(4)]
        random.shuffle(random_range)
        for num in random_range:
            neighbor = nearest_neighbors[num]
            if method == 'arrival' and not self.cluster_dict[neighbor].empty:
                return neighbor
            elif method == 'departure' and not self.cluster_dict[neighbor].full:
                return neighbor
        return None

    def change_time(self, time: timedelta):
        self.curr_time = time
        self.curr_tick = int((time.total_seconds() * self.tph) / 3600)

    def init_state(self, path: str, time=None):
        if time:
            self.change_time(time)
        df = pd.read_csv(path)
        for cluster in self.cluster_dict.values():
            cluster.curr_bikes = 0
        for station in self.station_data:
            if station not in df['name'].values:
                continue
            num_bikes = df.loc[df['name'] == station]['num_bikes_available'].values[0]
            self.cluster_dict[self.station_clusters[station]].curr_bikes += num_bikes
        self.fix_max_docks()

    def fix_max_docks(self):
        for cluster in self.cluster_dict.values():
            if cluster.curr_bikes > cluster.max_docks:
                cluster.max_docks = cluster.curr_bikes

    def mean_sq_error(self, cluster_dict=None, other_clusters=None, path=None):
        if other_clusters is None and path is None:
            print("No comparison stations provided")
            return
        if other_clusters is None:
            other_clusters = self.get_state(path)
        if cluster_dict is None:
            cluster_dict = self.cluster_dict
        error = 0
        for cluster in cluster_dict:
            error += (cluster_dict[cluster].curr_bikes - other_clusters[cluster]) ** 2
        return error / len(cluster_dict)

    def get_state(self, path: str):
        df = pd.read_csv(path)
        other_clusters = {i: 0 for i in range(len(self.clusters))}
        for i, cluster in zip(range(len(self.clusters)), self.clusters):
            for station in cluster:
                if station not in df['name'].values:
                    print(station, 'not in df')
                    continue
                other_clusters[i] += df.loc[df['name'] == station]['num_bikes_available'].values[0]
        return other_clusters

    def truncate_transitions(self):
        done = 0
        total = len(self.cluster_dict)
        for cluster in self.cluster_dict.values():
            cluster.truncate_transition()
            done += 1
            if done % 100 == 0:
                print(f'{done} of {total} done')
        print('StationClusters truncated')

    def cluster_stations(self, square_length: float):
        lat_min = np.inf
        lat_max = -np.inf
        lon_min = np.inf
        lon_max = -np.inf
        for station_name in self.station_data:
            station = self.station_data[station_name]
            if station['lat'] < lat_min:
                lat_min = station['lat']
            if station['lat'] > lat_max:
                lat_max = station['lat']
            if station['lon'] < lon_min:
                lon_min = station['lon']
            if station['lon'] > lon_max:
                lon_max = station['lon']
        self.vertical_squares = int((lat_max - lat_min) / square_length) + 1
        self.horizontal_squares = int((lon_max - lon_min) / square_length) + 1
        squares = self.horizontal_squares * self.vertical_squares
        print(f'{self.horizontal_squares} horizontal squares and '
              f'{self.vertical_squares} vertical squares. Total squares: {squares}')
        self.clusters = [[] for _ in range(squares)]
        for station_name in self.station_data:
            station = self.station_data[station_name]
            x = floor((station['lon'] - lon_min) / square_length)
            y = -floor((station['lat'] - lat_min) / square_length) - 1
            self.clusters[x + y * self.horizontal_squares].append(station_name)

        lat = lat_max - square_length / 2
        for i in range(self.vertical_squares):
            lon = lat_min + square_length / 2
            for j in range(self.horizontal_squares):
                self.clusters_lat_lon.append((lat, lon))
                lon += square_length
            lat -= square_length

        return self.horizontal_squares, self.vertical_squares, self.clusters

    def init_clusters(self, square_length=0.005):
        if not self.clusters:
            self.cluster_stations(square_length)
        if not self.station_clusters:
            self.station_clusters = {station: i for i in range(len(self.clusters)) for station in self.clusters[i]}
        for i in range(len(self.clusters)):
            cluster = self.clusters[i]
            if cluster:
                rate = [0 for i in range(24 * 4)]
                max_docks = 0
                transition = {i: {} for i in range(24 * 4)}
                neighbors_dist = {}
                for station in cluster:
                    max_docks += self.station_data[station]['max_docks']
                    for end_station in self.station_data[station]['dist']:
                        if end_station in neighbors_dist:
                            if self.station_data[station]['dist'][end_station] < neighbors_dist[end_station]:
                                neighbors_dist[end_station] = self.station_data[station]['dist'][end_station]
                        else:
                            neighbors_dist[end_station] = self.station_data[station]['dist'][end_station]
                    for tick in self.station_data[station]['rate']:
                        station_rate = self.station_data[station]['rate'][tick]
                        rate[tick] += station_rate
                        for end_station in self.station_data[station]['transition'][tick]:
                            if end_station in transition[tick]:
                                transition[tick][end_station] += (
                                        self.station_data[station]['transition'][tick][end_station] * station_rate)
                            else:
                                transition[tick][end_station] = (
                                        self.station_data[station]['transition'][tick][end_station] * station_rate)
                for tick in range(24 * 4):
                    for end_station in transition[tick]:
                        transition[tick][end_station] /= rate[tick]
                cluster_transition = self.get_cluster_transition(transition, cluster)
                cluster_dist = {}
                for station in neighbors_dist:
                    if station not in self.station_data:
                        continue
                    if self.station_clusters[station] in cluster_dist:
                        if neighbors_dist[station] < cluster_dist[self.station_clusters[station]]:
                            cluster_dist[self.station_clusters[station]] = neighbors_dist[station]
                    else:
                        cluster_dist[self.station_clusters[station]] = neighbors_dist[station]
                self.cluster_dict[i] = StationCluster(name=i,
                                                      neighbors_dist=cluster_dist,
                                                      max_docks=max_docks,
                                                      curr_bikes=0,
                                                      rate=rate,
                                                      transition=cluster_transition,
                                                      lat=self.clusters_lat_lon[i][0],
                                                      lon=self.clusters_lat_lon[i][1])

    def get_cluster_transition(self, transition: dict[int: dict[str: float]], cluster: int):
        cluster_transition = {i: {} for i in range(24 * 4)}
        for tick in transition:
            for end_station in transition[tick]:
                if end_station not in self.station_clusters:
                    # print(end_station, 'not in station_clusters')
                    continue
                if self.station_clusters[end_station] in cluster_transition[tick]:
                    cluster_transition[tick][self.station_clusters[end_station]] += transition[tick][end_station]
                else:
                    cluster_transition[tick][self.station_clusters[end_station]] = transition[tick][end_station]

            if len(cluster_transition[tick]) < 1:
                cluster_transition[tick] = {cluster: 1}
            prob_total = sum(cluster_transition[tick].values())
            if prob_total < 0.9999:
                for end_cluster in cluster_transition[tick]:
                    cluster_transition[tick][end_cluster] /= prob_total
        return cluster_transition

    def get_num_open_docks_in_clusters(self):
        dock_cluster = []
        for cluster in self.clusters:
            num_docks = 0
            for station in self.clusters[cluster]:
                num_docks += self.station_data[station]['max_docks'] - self.station_data[station]['curr_bikes']
            dock_cluster.append(num_docks)
        return dock_cluster

    def get_num_bikes_in_clusters(self) -> np.ndarray:
        num_bikes = []
        for i in range(len(self.clusters)):
            if i in self.cluster_dict:
                num_bikes.append(self.cluster_dict[i].curr_bikes)
            else:
                num_bikes.append(0)
        return np.array(num_bikes).reshape((self.vertical_squares, self.horizontal_squares))

    def show_bikes(self, save=False, name=None):
        plt.close()
        bikes = self.get_num_bikes_in_clusters()
        fig = sns.heatmap(bikes, cmap='Reds', vmin=0, vmax=250)
        plt.title(str(self.curr_time))
        if not name:
            name = str(self.curr_time.total_seconds())
        if save:
            plt.savefig('images/num_bikes/' + name + '.png')
        return fig

    def get_max_docks_in_clusters(self) -> np.ndarray:
        num_docks = []
        for i in range(len(self.clusters)):
            if i in self.cluster_dict:
                num_docks.append(self.cluster_dict[i].max_docks)
            else:
                num_docks.append(0)
        return np.array(num_docks).reshape((self.vertical_squares, self.horizontal_squares))

    def get_fill_percent(self):
        num_bikes = self.get_num_bikes_in_clusters()
        num_docks = self.get_max_docks_in_clusters()
        num_docks[num_docks == 0] = 1
        return num_bikes / num_docks

    def show_fill_percent(self, save=False, name=None):
        plt.close()
        fill = self.get_fill_percent()
        fig = sns.heatmap(fill, cmap='Reds', vmin=0, vmax=1)
        plt.title(str(self.curr_time))
        if not name:
            name = str(self.curr_time.total_seconds())
        if save:
            plt.savefig('images/fill/' + name + '.png')
        return fig
