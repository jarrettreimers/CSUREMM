import os.path
import time
import urllib.request, simplejson
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import query
import pickle
from old_model.station import Station


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


def get_rate(data: pd.DataFrame, days: list[datetime], tph: int) -> np.array:
    length = timedelta(hours=1 / tph)
    num_rates = int(timedelta(days=1).total_seconds() / length.total_seconds())
    total_arrivals = np.array([0 for tick in range(num_rates)])

    for day in days:
        intervals = cut(data, day, day + timedelta(days=1), length)
        total_arrivals += np.array([len(df) for df in intervals])
    total_arrivals = total_arrivals / len(days)
    return total_arrivals


def get_transition(data: pd.DataFrame, days: list[datetime], tph: int, truncate=False, whitelist=None) -> \
        tuple[list, list[dict[str, float]]]:
    if not len(data):
        print
        return [], []
    length = timedelta(hours=1 / tph)
    if whitelist is None:
        unique_stations = data['end_station_name'].unique()  # get all unique stations
        for i in range(len(unique_stations)):
            if unique_stations[i].__contains__('Avenue'):
                data.loc[data['end_station_name'] == unique_stations[i], 'end_station_name'] = unique_stations[
                    i].replace('Avenue', 'Ave')
                unique_stations[i] = unique_stations[i].replace('Avenue', 'Ave')
                print('renamed', unique_stations[i], 'to', unique_stations[i].replace('Avenue', 'Ave'))
    else:
        unique_stations = whitelist

    stations_transition_by_tick = [{station: 0 for station in unique_stations} for tick in range(24 * tph)]
    trip_count = [0] * 24 * tph

    for day in days:
        end_time = day + timedelta(days=1)
        data_list = cut(data, day, end_time, length)
        for i in range(len(data_list)):
            total_trips = 0
            for transition_station in data_list[i]['end_station_name'].unique():
                if whitelist is not None and transition_station not in whitelist:
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


def get_station(station: str, station_information: pd.DataFrame, start_date: datetime, end_date: datetime, tph=1,
                weekday=True, max_docks=30, curr_bikes=15, whitelist=None) -> Station:
    if (end_date.year - start_date.year) != 0:
        print('Error, dates must be in same year!')
        return None
    now = time.time()
    data = pd.read_csv(f'data/{start_date.year}/by_station/{station}.csv', low_memory=False, index_col=0)
    data.dropna(axis="rows", inplace=True)
    data = query.make_datetime(data)
    days = get_weekdays_and_weekends(start_date=start_date, end_date=end_date)
    data = query.select_time(data, start_date, end_date)
    print(len(data), 'rows loaded in', time.time() - now, 'seconds')

    if weekday:
        days = days[0]
    else:
        days = days[1]

    neighbors_dist = {}
    neighbors_names, transition = get_transition(data=data, days=days, tph=tph, whitelist=whitelist)
    rate = get_rate(data=data, days=days, tph=tph)
    for dest_station in neighbors_names:
        neighbors_dist[dest_station] = (
                data.loc[data['end_station_name'] == dest_station]['ended_at'] -
                data.loc[data['end_station_name'] == dest_station]['started_at']).mean()
    max_docks = station_information.loc[station_information['name'] == station]['capacity'].values[0]
    lat = station_information.loc[station_information['name'] == station]['lat'].values[0]
    lon = station_information.loc[station_information['name'] == station]['lon'].values[0]

    print(f'Loaded {station} in {time.time() - now} seconds')

    return Station(name=station,
                   id=0,
                   neighbors_dist=neighbors_dist,
                   neighbors_names=neighbors_names,
                   rate=rate,
                   transition=transition,
                   max_docks=max_docks,
                   curr_bikes=curr_bikes,
                   lat=lat,
                   lon=lon)


def pickle_station(station: Station, path='data/station_data/test_parameters/'):
    station_data = {'station_name': station.name, 'id': station.id, 'neighbors_dist': station.neighbors_dist,
                    'neighbors_names': station.neighbors_names, 'rate': station.rate, 'transition': station.transition,
                    'max_docks': station.max_docks, 'curr_bikes': station.curr_bikes, 'lat': station.lat,
                    'lon': station.lon}
    with open(f'{path}{station.name}.pickle', 'wb') as handle:
        pickle.dump(station_data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def get_pickle_station(station: str, path: str) -> Station:
    with open(f'{path}{station}.pickle', 'rb') as handle:
        station_data = pickle.load(handle)
    return Station(name=station,
                   id=0,
                   neighbors_dist=station_data['neighbors_dist'],
                   neighbors_names=station_data['neighbors_names'],
                   rate=station_data['rate'],
                   transition=station_data['transition'],
                   max_docks=station_data['max_docks'],
                   curr_bikes=station_data['curr_bikes'],
                   lat=station_data['lat'],
                   lon=station_data['lon'])

def get_state_df(station_information: list[dict[str: str]], path: str):
    with open(path, 'r') as f:
        station_status = simplejson.load(f)

    flat_data = []
    for station in station_information:
        for station_stat in station_status['data']['stations']:
            if station['station_id'] == station_stat['station_id']:
                flat_station = {
                    'name': station['name'],
                    'capacity': station['capacity'],
                    'station_id': station['station_id'],
                    'lat': station['lat'],
                    'lon': station['lon'],
                    'num_bikes_available': station_stat['num_bikes_available'],
                    'num_bikes_disabled': station_stat['num_bikes_disabled'],
                    'num_docks_available': station_stat['num_docks_available'],
                    'num_docks_disabled': station_stat['num_docks_disabled'],
                    'operating': station_stat['is_renting'] and station_stat['is_returning'] and station_stat[
                        'is_installed'],
                }
                flat_data.append(flat_station)
                break
    df = pd.DataFrame(flat_data)
    return df


def get_station_information(save=False):
    station_information = simplejson.load(
        urllib.request.urlopen('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_information.json'))
    station_status = simplejson.load(
        urllib.request.urlopen('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json'))

    stations = station_information['data']['stations']
    flat_data = []

    for station in stations:
        for station_stat in station_status['data']['stations']:
            if station['station_id'] == station_stat['station_id']:
                region_id = None
                if 'region_id' in station:
                    region_id = station['region_id']
                flat_station = {
                    'name': station['name'],
                    'capacity': station['capacity'],
                    'station_id': station['station_id'],
                    'short_name': station['short_name'],
                    'region_id': region_id,
                    'lat': station['lat'],
                    'lon': station['lon'],
                    'num_bikes_available': station_stat['num_bikes_available'],
                    'num_bikes_disabled': station_stat['num_bikes_disabled'],
                    'num_docks_available': station_stat['num_docks_available'],
                    'num_docks_disabled': station_stat['num_docks_disabled'],
                    'operating': station_stat['is_renting'] and station_stat['is_returning'] and station_stat[
                        'is_installed'],
                }
                flat_data.append(flat_station)
                break
    df = pd.DataFrame(flat_data)
    if save:
        now = datetime.now()
        path = f'data/station_data/status_at_time/{now.year}_{now.month}_{now.day}_{now.hour}:{now.minute}.csv'
        df.to_csv(path)
    return df
