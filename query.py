import pandas as pd
import datetime 

class Query():
  def __init__(self)

  def get_datetime(self, year, month, day, hour, minute, second):
    return datetime.datetime(year, month, day, hour, minute, second)
  
  def select_time(self, data: pd.DataFrame, start_time: datetime.datetime, end_time: datetime.datetime):
    return data.loc[data['starttime'] >= start_time].loc[data['starttime'] <= end_time]
