import datetime
from pandas import DataFrame
import query


def cut(df: DataFrame, start_time: datetime.datetime, stop_time: datetime.datetime, length: datetime.timedelta) \
        -> list[DataFrame]:
    total_length = stop_time - start_time
    # in minutes
    bins = int((total_length.total_seconds() / length.total_seconds()))
    dfs = []
    for i in range(bins):
        dfs.append(query.select_time(df, start_time + (i * length), start_time + ((i + 1) * length)))
    return dfs


def get_weekdays_and_weekends(start_date: datetime.datetime, stop_time: datetime.datetime) -> list[list[datetime.datetime]]:
    weekdays = []
    weekends = []
    i = 0
    day = start_date
    while day <= stop_time:
        if day.date().weekday() < 5:
            weekdays.append(day)
        else:
            weekends.append(day)
        day += datetime.timedelta(days=1)
    return [weekdays, weekends]