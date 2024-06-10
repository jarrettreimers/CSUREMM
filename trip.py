class Trip:
    def __init__(self,
                 start_station: str,
                 end_station: str,
                 travel_time: float,
                 ):
        self.start_station = start_station
        self.end_station = end_station
        self.travel_time = travel_time
        self.curr_time = 0

    def update(self, time: float) -> bool:
        self.curr_time += time
        if self.curr_time > self.travel_time:
            return True
        return False

    def print(self):
        print(self.start_station, 'to', self.end_station, 'in', self.travel_time, 'with', self.curr_time, 'completed')
