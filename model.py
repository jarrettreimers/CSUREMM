from typing import List

from numpy.random import poisson, choice
from station import Station
from trip import Trip

class Model:
    def __init__(self,
                 station_list: [],
                 stations: {str: Station},
                 in_transit: List[Trip]
                 ):
        """
        :param station_list: Ordered list of stations - corresponds to transition vector prob from station to station
        :param stations: Names of stations that point to Station objects
        :param in_transit: List of trips in transit
        """
        self.station_list = station_list
        self.stations = stations
        self.in_transit = in_transit
        self.curr_time = 0

    def sim(self, time=1):
        """

        :param time: Timestep with length t, 24/t steps in a day
        :return:
        """
        self.curr_time += time
        transit = []
        for trip in self.in_transit:
            if trip.update(time):
                if not self.stations[trip.end_station].return_bike(trip):
                    print('Failure to dock') # TODO handle dock failure
                    trip.print()
            else:
                transit.append(trip)

        for station_name in self.stations:
            station = self.stations[station_name]
            departures = poisson(station.rate[self.curr_time])
            end_trips = choice(self.station_list, departures, p=station.transition)
            for departure_name in end_trips:
                trip = Trip(station_name, departure_name, station.neighbors_dist[departure_name])
                if not station.get_bike(trip):
                    print('Failure to depart') # TODO handle departure failure
                    trip.print()
                else:
                    transit.append(trip)
        self.in_transit = transit


