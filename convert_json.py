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


def get_filtered_stations(json_file_path):
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)

    stations = json_data['data']['stations']

    flat_data = []
    for station in stations:
        if station['capacity'] > 12:  # Filter condition
            flat_station = {
                'name': station['name'],
                'capacity': station['capacity'],
                'short_name': station['short_name']
            }
            flat_data.append(flat_station)

    df = pd.DataFrame(flat_data)
    return df
