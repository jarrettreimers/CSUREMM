import pandas as pd

from trip import Trip


# def create_station(name: str, year: str) -> Station:
#     df = pd.read_csv(f'data/{year}/by_station/{name}.csv')
#     id = df['station_id'].iloc[0]


class Station:
    def __init__(self,
                 name: str,
                 id: float,
                 neighbors_dist: dict,
                 nearest_neighbors: list,
                 max_docks: int,
                 curr_bikes: int,
                 rate: [float],
                 transition: [],
                 ):

        self.name = name
        self.id = id
        self.neighbors_dist = neighbors_dist
        self.nearest_neighbors = nearest_neighbors
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
        return False

    def return_bike(self, trip: Trip) -> bool:
        if not self.full:
            self.curr_bikes += 1
            if self.curr_bikes == self.max_docks:
                self.full = True
            return True
        self.bad_arrivals.append(trip)
        return False

    def get_nearest_neighbor(self) -> list:
        return self.nearest_neighbors

    def update(self):
        self.empty = self.curr_bikes == 0
        self.full = self.curr_bikes == self.max_docks
