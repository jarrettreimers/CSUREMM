import pandas as pd


class Stations:
    def __init__(self):
        self.stations_id = {}
        self.stations_count = {}

    def clear_data(self):
        self.stations_id = {}
        self.stations_count = {}

    def add_data(self, data: pd.DataFrame):
        stations = set(data['start station id']).union(set(data['end station id']))

        for station in stations:
            if station not in self.stations_count:
                self.stations_count[station] = 0
            self.stations_count[station] -= len(data.loc[data['start station id'] == station])
            self.stations_count[station] += len(data.loc[data['end station id'] == station])
