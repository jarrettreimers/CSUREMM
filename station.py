import pandas as pd
from trip import Trip


class Station:
    def __init__(self,
                 name: str,
                 id: float,
                 neighbors_dist: dict,
                 neighbors_names: list,
                 max_docks: int,
                 curr_bikes: int,
                 rate: list[float],
                 transition: list[dict],
                 ):

        self.name = name
        self.id = id
        self.neighbors_dist = neighbors_dist
        self.neighbors_names = neighbors_names
        self.nearest_neighbors = sorted(neighbors_dist, key=neighbors_dist.get)
        self.max_docks = max_docks
        self.curr_bikes = curr_bikes
        self.empty = curr_bikes == 0
        self.full = curr_bikes == max_docks
        self.rate = rate
        self.transition = transition
        self.bad_arrivals = []
        self.bad_departures = []

    def get_bike(self, trip: Trip) -> bool:
        if not self.empty:
            self.curr_bikes -= 1
            if self.curr_bikes == 0:
                self.empty = True
            return True
        self.bad_departures.append(trip)
        self.update()
        return False

    def return_bike(self, trip: Trip) -> bool:
        if not self.full:
            self.curr_bikes += 1
            if self.curr_bikes == self.max_docks:
                self.full = True
            return True
        self.bad_arrivals.append(trip)
        self.update()
        return False

    def update(self):
        self.empty = self.curr_bikes == 0
        self.full = self.curr_bikes == self.max_docks