class Station:
    def __init__(self,
                 name: str,
                 id: float,
                 neighbors_dist: dict,
                 nearest_neighbors: list,
                 max_docks: int,
                 curr_bikes: int,
                 full: bool,
                 empty: bool,
                 rate: [float],
                 transition: [],
                 ):

        self.name = name
        self.id = id
        self.neighbors_dist = neighbors_dist
        self.nearest_neighbors = nearest_neighbors
        self.max_docks = max_docks
        self.curr_bikes = curr_bikes
        self.empty = empty
        self.full = full
        self.rate = rate
        self.transition = transition

    def get_bike(self):
        if not self.empty:
            self.curr_bikes -= 1
            if self.curr_bikes == 0:
                self.empty = True
            return True
        return False

    def return_bike(self):
        if not self.full:
            self.curr_bikes += 1
            if self.curr_bikes == self.max_docks:
                self.full = True
            return True
        return False

    def get_nearest_neighbor(self):
        return self.nearest_neighbors
