import requests
import copy
import json
import os
from os.path import join as pjoin
curw_station_meta_struct = {
    'stationId': '',
    'name': '',
    'station_meta': [],
    'source': '',
    'type': '',
    'variables': [],
    'units': [],
    'max_values': [],
    'min_values': [],
    'description': '',
    'run_name': '',
}
curw_obs_station_meta_struct = {
    'stationId': '',
    'name': '',
    'station_meta': [],
    'source': '',
    'type': '',
    'variables': [],
    'units': [],
    'unit_type': [],
    'max_values': [],
    'min_values': [],
    'description': '',
    'run_name': '',
}

def get_station_hash_map(stations):
    hash_map = {}
    for station in stations:
        if station.get('stationId', None) is not None:
            hash_map[station.get('stationId')] = station
        # HACK: Handle stations which are not configure with `stationId` that we wanted
        if 'station_alias' in station and station.get('station_alias', None) is not None:
            hash_map[station.get('station_alias')] = station

    return hash_map


def forward_to_weather_underground(data, logger):
    r = requests.get('https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php', params=data)
    logger.debug('WeatherUnderground >> %s, %s', r.status_code, r.text)


def forward_to_dialog_iot(data, logger):
    r = requests.get('http://h.a.ideabiz.lk/weatherstation/updateweatherstation.php', params=data)
    logger.debug('Dialog IoT >> %s, %s', r.status_code, r.text)


def add_station_curw_iot(data, logger_bulk):
    global curw_station_metaseries
    logger_bulk.error("dataaa %s" %data)

    root_dir = os.path.dirname(os.path.realpath(__file__))
    logger_bulk.error(root_dir)

    CONFIG = json.loads(open(pjoin(root_dir, '../config/StationConfig.json')).read())
    logger_bulk.error(data['stationId'])

    stations = CONFIG['stations']

    for station_data in data:

        if not any(station['stationId'] == station_data['stationId'] for station in stations):

            curw_station_metaseries = copy.deepcopy(curw_station_meta_struct)
            curw_station_metaseries['stationId'] = station_data['stationId']
            curw_station_metaseries['name'] = station_data['name']
            curw_station_metaseries['station_meta'] = station_data['station_meta']
            curw_station_metaseries['source'] = station_data['source']
            curw_station_metaseries['type'] = station_data['type']
            curw_station_metaseries['variables'] = station_data['variables']
            curw_station_metaseries['units'] = station_data['units']
            curw_station_metaseries['max_values'] = station_data['max_values']
            curw_station_metaseries['min_values'] = station_data['min_values']
            curw_station_metaseries['description'] = station_data['description']
            curw_station_metaseries['run_name'] = station_data['run_name']

            with open("../config/StationConfig.json", "w") as outfile:
                outfile.write(curw_station_metaseries)
        else:
            logger_bulk.error("%s station already exist" % data['stationId'])




