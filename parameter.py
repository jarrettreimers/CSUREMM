import datetime
import pandas as pd
import numpy as np
import query


def cut(df: pd.DataFrame, start_time: datetime.datetime, stop_time: datetime.datetime, length: datetime.timedelta) \
        -> list[pd.DataFrame]:
    total_length = stop_time - start_time
    # in minutes
    bins = int((total_length.total_seconds() / length.total_seconds()))
    cut_df = query.select_time(df, start_time, stop_time)
    dfs = []
    for i in range(bins):
        dfs.append(query.select_time(cut_df, start_time + (i * length), start_time + ((i + 1) * length)))
    return dfs


def get_weekdays_and_weekends(start_date: datetime.datetime, end_date: datetime.datetime) -> list[
    list[datetime.datetime]]:
    weekdays = []
    weekends = []
    i = 0
    day = start_date
    while day <= end_date:
        if day.date().weekday() < 5:
            weekdays.append(day)
        else:
            weekends.append(day)
        day += datetime.timedelta(days=1)
    return [weekdays, weekends]


def get_rate(station: str, start_date: datetime.datetime, end_date: datetime.datetime, length: datetime.timedelta,
             weekday=True) -> np.array:
    if (end_date.year - start_date.year) != 0:
        print('Error, rate must be in same year')
        return np.array(0)
    df = pd.read_csv(f'data/{start_date.year}/by_station/{station}.csv')
    df = query.make_datetime(df)
    df = df.loc[(df['started_at'] >= start_date) & (df['started_at'] <= end_date)]

    days_ends = get_weekdays_and_weekends(start_date, end_date)
    if weekday:
        days = days_ends[0]
    else:
        days = days_ends[1]

    num_rates = int(datetime.timedelta(days=1).total_seconds() / length.total_seconds())
    total_arrivals = np.array([0 for i in range(num_rates)])

    for day in days:
        intervals = cut(df, day, day + datetime.timedelta(days=1), length)
        total_arrivals += np.array([len(df) for df in intervals])
    total_arrivals = total_arrivals/len(days)
    return total_arrivals

# def gen_station_transition(name: str, rate_interval=1, year=2023, start_month=5, end_month=6, weekday) -> Station:
#     station_df = pd.read_csv(f'data/{year}/by_station/{name}.csv', index_col=0)
#     cut()
