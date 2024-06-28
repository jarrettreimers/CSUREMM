from trip import Trip


class StationCluster:
    def __init__(self,
                 name: int,
                 neighbors_dist: dict,
                 max_docks: int,
                 curr_bikes: int,
                 rate: dict[int: float],
                 transition: dict[int: [dict[str: float]]],
                 ):
        self.name = name
        self.neighbors_dist = neighbors_dist
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
        self.empty = self.curr_bikes <= 0
        self.full = self.curr_bikes >= self.max_docks

    def truncate_transition(self, method='uniform*1/2'):
        if method == 'uniform*1/2':
            self.truncate_transition_uniform()
        else:
            self.truncate_transition_fixed(method)

    def truncate_transition_fixed(self, method):
        pass

    def truncate_transition_uniform(self):
        for tick in self.transition:
            uniform_prob_2 = 1 / len(self.transition[tick]) * 2
            total_prob = 0
            remove = []
            for end_station in self.transition[tick]:
                if self.transition[tick][end_station] < uniform_prob_2:
                    total_prob += self.transition[tick][end_station]
                    remove.append(end_station)
            for end_station in remove:
                del self.transition[tick][end_station]
            for end_station in self.transition[tick]:
                self.transition[tick][end_station] = self.transition[tick][end_station] / (1 - total_prob)
