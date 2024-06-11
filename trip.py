class Trip:
    def __init__(self,
                 start_station: str,
                 end_station: str,
                 start_time: float,
                 trip_time: float,
                 ):
        self.start_station = start_station
        self.end_station = end_station
        self.start_time = start_time
        self.curr_time = start_time
        self.end_time = start_time+trip_time

    def update(self, time: float) -> bool:
        self.curr_time += time
        if self.curr_time > self.end_time:
            return True
        return False

    def print(self):
        print(self.start_station, 'to', self.end_station, 'at', self.start_time, 'to', self.end_time, 'completed')
