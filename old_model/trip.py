from datetime import timedelta

class Trip:
    def __init__(self,
                 start_station: str,
                 end_station: str,
                 start_time: timedelta,
                 trip_time: timedelta,
                 ):
        self.start_station = start_station
        self.end_station = end_station
        # if end_station.__contains__('Avenue'):
        #     self.end_station = self.end_station.replace('Avenue', 'Ave')
        self.start_time = start_time
        self.curr_time = start_time
        self.end_time = start_time+trip_time

    def update(self, time: timedelta) -> bool:
        """
        :param time:
        :return: True if trip completed, else False
        """
        self.curr_time += time
        # print('current: ', self.curr_time, '\nstart: ', self.start_time, '\n end: ', self.end_time)
        if self.curr_time > self.end_time:
            return True
        return False

    def print(self):
        print(self.start_station, 'to', self.end_station, 'at', self.start_time, 'to', self.end_time, 'completed')
