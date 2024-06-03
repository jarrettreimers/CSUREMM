import pandas as pd
import datetime


def get_datetime(year, month, day, hour, minute, second) -> datetime.datetime:
    return datetime.datetime(year, month, day, hour, minute, second)


def select_time(data: pd.DataFrame, start_time: datetime.datetime,
                end_time: datetime.datetime) -> pd.DataFrame:
    return data.loc[data['starttime'] >= start_time].loc[data['starttime'] <= end_time]


def get_stations(data: pd.DataFrame) -> set:
    return set(data['start station id']).union(set(data['end station id']))


def select_start_station(data: pd.DataFrame, station_id: int) -> pd.DataFrame:
    return data.loc[data['start station id'] == station_id]

def select_end_station(data: pd.DataFrame, station_id: int) -> pd.DataFrame:
    return data.loc[data['end station id'] == station_id]
