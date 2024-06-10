import pandas as pd
import datetime


def get_datetime(year, month, day, hour, minute, second) -> datetime.datetime:
    return datetime.datetime(year, month, day, hour, minute, second)


def select_time(data: pd.DataFrame, start_time: datetime.datetime,
                end_time: datetime.datetime) -> pd.DataFrame:
    return data.loc[data['started_at'] >= start_time].loc[data['started_at'] <= end_time]


def get_stations(data: pd.DataFrame) -> set:
    return set(data['start_station_id']).union(set(data['end_station_id']))


def select_start_station(data: pd.DataFrame, station_id: int) -> pd.DataFrame:
    return data.loc[data['start station id'] == station_id]

def select_end_station(data: pd.DataFrame, station_id: int) -> pd.DataFrame:
    return data.loc[data['end station id'] == station_id]
