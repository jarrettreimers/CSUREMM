import pandas as pd
import json

json_data = pd.read_json('station_information.json')
stations = json_data['data']['stations']
flat_data = []

for station in stations:
    flat_station = {
        'name': station['name'],
        'capacity': station['capacity'],
        'short_name': station['short_name']
    }
    flat_data.append(flat_station)

df = pd.DataFrame(flat_data)
print(df)
