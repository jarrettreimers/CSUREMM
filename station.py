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
                 transition: list[dict[str: float]],
                 lat: float,
                 lon: float,
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
        self.lat = lat
        self.lon = lon

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

    def refine_by_3(self):
        new_rate = []
        new_transition = []
        for i in range(len(self.rate) - 1):
            new_rate += ([1 / 3 * (self.rate[i]), 1 / 3 * (2 / 3 * self.rate[i] + 1 / 3 * self.rate[i + 1]),
                          1 / 3 * (1 / 3 * self.rate[i] + 2 / 3 * self.rate[i + 1])])
        self.rate = new_rate
        for i in range(len(self.transition)):
            new_transition += [self.transition[i], self.transition[i].copy(), self.transition[i].copy()]
        self.transition = new_transition

    def remove_transition(self, neighbor: str):
        for i in range(len(self.neighbors_names)):
            if self.neighbors_names[i] == neighbor:
                for j in range(len(self.transition)):
                    prob = self.transition[j].pop(i)
                    if prob != 0 and prob != 1:
                        self.transition[j] = [p / (1 - prob) for p in self.transition[j]]
                break

    def remove_neighbor(self, neighbor: str):
        self.neighbors_dist.pop(neighbor)
        self.nearest_neighbors = sorted(self.neighbors_dist, key=self.neighbors_dist.get)
        self.remove_transition(neighbor)
        self.neighbors_names.remove(neighbor)

    def truncate_transition(self):
        uniform_prob = 1 / len(self.neighbors_names)
        for i in range(len(self.transition)):
            total_prob = 0
            for j in range(len(self.transition[i])):
                if 0 < self.transition[i][j] < uniform_prob:
                    total_prob += self.transition[i][j]
                    self.transition[i][j] = 0
            self.transition[i] = [p / (1 - total_prob) for p in self.transition[i]]

    def cluster(self, square_length: float):
        for neighbor in self.neighbors_names:
            if self.neighbors_dist[neighbor] < square_length:
                self.remove_neighbor(neighbor)