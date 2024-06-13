from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import query
from station import Station


def cut(df: pd.DataFrame, start_time: datetime, stop_time: datetime, length: timedelta) \
        -> list[pd.DataFrame]:
    total_length = stop_time - start_time
    # in minutes
    bins = int((total_length.total_seconds() / length.total_seconds()))
    cut_df = query.select_time(df, start_time, stop_time)
    dfs = []
    for i in range(bins):
        dfs.append(query.select_time(cut_df, start_time + (i * length), start_time + ((i + 1) * length)))
    return dfs


def get_weekdays_and_weekends(start_date: datetime, end_date: datetime) -> list[list[datetime]]:
    weekdays = []
    weekends = []
    day = start_date
    while day <= end_date:
        if day.date().weekday() < 5:
            weekdays.append(day)
        else:
            weekends.append(day)
        day += timedelta(days=1)
    return [weekdays, weekends]


def get_rate(station: str, start_date: datetime, end_date: datetime, tph: int, weekday=True) -> np.array:
    if (end_date.year - start_date.year) != 0:
        print('Error, rate must be in same year')
        return np.array(0)
    length = timedelta(hours=1 / tph)

    df = pd.read_csv(f'data/{start_date.year}/by_station/{station}.csv', low_memory=False, index_col=0)
    df = query.make_datetime(df)
    df = df.loc[(df['started_at'] >= start_date) & (df['started_at'] <= end_date)]

    days_ends = get_weekdays_and_weekends(start_date, end_date)
    if weekday:
        days = days_ends[0]
    else:
        days = days_ends[1]

    num_rates = int(timedelta(days=1).total_seconds() / length.total_seconds())
    total_arrivals = np.array([0 for tick in range(num_rates)])

    for day in days:
        intervals = cut(df, day, day + timedelta(days=1), length)
        total_arrivals += np.array([len(df) for df in intervals])
    total_arrivals = total_arrivals / len(days)
    return total_arrivals


def get_rate_new(data: pd.DataFrame, days: list[datetime], tph: int) -> np.array:
    length = timedelta(hours=1 / tph)
    num_rates = int(timedelta(days=1).total_seconds() / length.total_seconds())
    total_arrivals = np.array([0 for tick in range(num_rates)])

    for day in days:
        intervals = cut(data, day, day + timedelta(days=1), length)
        total_arrivals += np.array([len(df) for df in intervals])
    total_arrivals = total_arrivals / len(days)
    return total_arrivals


def get_transition(station: str, start_date: datetime, end_date: datetime, tph: int,
                   whitelist_stations=None) -> np.array:
    if whitelist_stations is None:
        whitelist_stations = ['E 7 St & Ave B',
                              'Cooper Square & Astor Pl',
                              'E 7 St & Ave C',
                              'Ave A & E 14 St',
                              'W 21 St & 6 Ave']
    data = pd.read_csv(f'data/2023/by_station/{station}.csv', low_memory=False, index_col=0)
    data.dropna(axis="rows", inplace=True)
    data = query.make_datetime(data)
    length = timedelta(hours=1 / tph)
    cut_df = query.select_time(data, start_date, end_date)
    unique_stations = whitelist_stations  # CHANGE EVENTUALLY
    stations_transition_by_tick = [{station: 0 for station in unique_stations} for tick in range(24 * tph)]
    trip_count = [0] * 24 * tph

    weekdays = get_weekdays_and_weekends(start_date, end_date)[0]
    for day in weekdays:
        end_time = day + timedelta(days=1)
        cut_list = cut(cut_df, day, end_time, length)
        for i in range(len(cut_list)):
            total_trips = 0
            for transition_station in cut_list[i]['end_station_name'].unique():
                if transition_station not in whitelist_stations:
                    continue
                station_trips = len(cut_list[i].loc[cut_list[i]['end_station_name'] == station])
                total_trips += station_trips
                if transition_station in stations_transition_by_tick[i]:
                    stations_transition_by_tick[i][transition_station] += station_trips
                else:
                    stations_transition_by_tick[i][transition_station] = station_trips
            trip_count[i] += total_trips
    transitions = []
    for tick in range(len(stations_transition_by_tick)):
        tick_transition = []
        if trip_count[tick] == 0:
            trip_count[tick] = 1
            stations_transition_by_tick[tick][station] = 1
        for transition_station in unique_stations:
            tick_transition.append(stations_transition_by_tick[tick][transition_station] / trip_count[tick])
        transitions.append(tick_transition)

    return [unique_stations, transitions]


def get_transition_new(data: pd.DataFrame, days: list[datetime], tph: int, whitelist_stations=None) -> tuple[
    list, list]:
    length = timedelta(hours=1 / tph)
    unique_stations = data['end_station_name'].unique()
    stations_transition_by_tick = [{station: 0 for station in unique_stations} for tick in range(24 * tph)]
    trip_count = [0] * 24 * tph

    for day in days:
        end_time = day + timedelta(days=1)
        data_list = cut(data, day, end_time, length)
        for i in range(len(data_list)):
            total_trips = 0
            for transition_station in data_list[i]['end_station_name'].unique():
                if whitelist_stations is not None and transition_station not in whitelist_stations:
                    continue
                station_trips = len(data_list[i].loc[data_list[i]['end_station_name'] == transition_station])
                total_trips += station_trips
                stations_transition_by_tick[i][transition_station] += station_trips
            trip_count[i] += total_trips
    transitions = []
    for tick in range(len(stations_transition_by_tick)):
        tick_transition = []
        if trip_count[tick] == 0:
            trip_count[tick] = 1
            stations_transition_by_tick[tick][data['start_station_name'].iloc[0]] = 1
        for transition_station in unique_stations:
            tick_transition.append(stations_transition_by_tick[tick][transition_station] / trip_count[tick])
        transitions.append(tick_transition)

    return unique_stations, transitions


def avg_travel_time(orig_station: str, dest_station: str):
    data = pd.read_csv(f'data/2023/by_station/{orig_station}.csv', low_memory=False, index_col=0)
    data.dropna(axis="rows", inplace=True)
    data = data.loc[data['end_station_name'] == dest_station]
    data = query.make_datetime(data)
    return (data['ended_at'] - data['started_at']).mean()


def fast_station(station: str, start_date: datetime, end_date: datetime, tph=1, weekday=True,
                 max_docks = 30, curr_bikes = 15) -> Station:
    if (end_date.year - start_date.year) != 0:
        print('Error, dates must be in same year!')
        return None
    data = pd.read_csv(f'data/2023/by_station/{station}.csv', low_memory=False, index_col=0)
    data.dropna(axis="rows", inplace=True)
    data = query.make_datetime(data)
    days = get_weekdays_and_weekends(start_date=start_date, end_date=end_date)

    if weekday:
        days = days[0]
    else:
        days = days[1]

    neighbors_dist = {}
    neighbors_names, transition = get_transition_new(data=data, days=days, tph=tph)
    rate = get_rate_new(data=data, days=days, tph=tph)
    for dest_station in neighbors_names:
        neighbors_dist[dest_station] = (
                data.loc[data['end_station_name'] == dest_station]['ended_at'] -
                data.loc[data['end_station_name'] == dest_station]['started_at']).mean()

    return  Station(name=station,
                    id=0,
                    neighbors_dist=neighbors_dist,
                    neighbors_names=neighbors_names,
                    rate=rate,
                    transition=transition,
                    max_docks=max_docks,
                    curr_bikes=curr_bikes)
