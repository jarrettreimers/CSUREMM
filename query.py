import pandas as pd
import datetime 

class Query():
  def get_datetime(self, year, month, day, hour, minute, second) -> datetime.datetime:
    return datetime.datetime(year, month, day, hour, minute, second)
  
  def select_time(self, data: pd.DataFrame, start_time: datetime.datetime, end_time: datetime.datetime) -> pd.DataFrame:
    return data.loc[data['starttime'] >= start_time].loc[data['starttime'] <= end_time]
