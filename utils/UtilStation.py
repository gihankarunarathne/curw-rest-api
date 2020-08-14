import requests
import copy
import json
import os
from os.path import join as pjoin
from datetime import datetime

now_date = datetime.now()
COMMON_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
date = now_date.strftime(COMMON_DATE_FORMAT)

root_dir = os.path.dirname(os.path.realpath(__file__))

CONFIG_curwiot_station = json.loads(open(pjoin(root_dir, '../config/StationConfig.json')).read())
CONFIG_curw_station = json.loads(open(pjoin(root_dir, '../../ExtractAndPush/CONFIG.dist.json')).read())
CONFIG_curwobs_station = json.loads(open(pjoin(root_dir, '../../Data-Pusher-Obs/CONFIG.dist.json')).read())

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


def get_station_metaseries(station_type, db_type, station_data, logger_bulk):

    if station_type == 'weather_stations':

        if db_type == 'curw_iot':
            station_metaseries = copy.deepcopy(curw_station_meta_struct)
            station_metaseries['stationId'] = station_data['stationId']
            station_metaseries['name'] = station_data['name']
            station_metaseries['station_meta'] = station_data['station_meta']
            station_metaseries['source'] = station_data['source']
            station_metaseries['type'] = station_data['type']
            station_metaseries['variables'] = station_data['variables']
            station_metaseries['units'] = station_data['units']
            station_metaseries['max_values'] = station_data['max_values']
            station_metaseries['min_values'] = station_data['min_values']
            station_metaseries['description'] = station_data['description']
            station_metaseries['run_name'] = station_data['run_name']

            return station_metaseries

        if db_type == 'curw_obs':
            station_metaseries = copy.deepcopy(curw_obs_station_meta_struct)
            station_metaseries['stationId'] = station_data['stationId']
            station_metaseries['name'] = station_data['name']
            station_metaseries['station_meta'] = station_data['station_meta']
            station_metaseries['source'] = station_data['source']
            station_metaseries['type'] = station_data['type']
            station_metaseries['variables'] = ["Precipitation", "Temperature", "WindSpeed", "WindDirection", "Humidity", "Pressure"]
            station_metaseries['units'] = ["mm", "oC", "m/s", "degrees", "%", "mmHg"]
            station_metaseries['unit_type'] = ["Accumulative", "Instantaneous", "Instantaneous", "Instantaneous", "Instantaneous", "Instantaneous"]
            station_metaseries['max_values'] = ["120", "40", "30", "360", "100", "900"]
            station_metaseries['min_values'] = ["0", "0", "0", "0", "0", "600"]
            station_metaseries['description'] = station_data['description']
            station_metaseries['run_name'] = station_data['run_name']

            return station_metaseries

    if station_type == 'water_level_stations':
        if db_type == 'curw_iot':
            station_metaseries = copy.deepcopy(curw_station_meta_struct)
            station_metaseries['stationId'] = station_data['stationId']
            station_metaseries['name'] = station_data['name']
            station_metaseries['station_meta'] = station_data['station_meta']
            station_metaseries['source'] = station_data['source']
            station_metaseries['type'] = station_data['type']
            station_metaseries['variables'] = station_data['variables']
            station_metaseries['units'] = station_data['units']
            station_metaseries['max_values'] = station_data['max_values']
            station_metaseries['min_values'] = station_data['min_values']
            station_metaseries['description'] = station_data['description']
            station_metaseries['run_name'] = station_data['run_name']
            station_metaseries['mean_sea_level'] = station_data['mean_sea_level']
            station_metaseries['min_wl'] = station_data['min_wl']
            station_metaseries['max_wl'] = station_data['max_wl']

            return station_metaseries

        if db_type == 'curw_obs':
            station_metaseries = copy.deepcopy(curw_obs_station_meta_struct)
            station_metaseries['stationId'] = station_data['stationId']
            station_metaseries['name'] = station_data['name']
            station_metaseries['station_meta'] = station_data['station_meta']
            station_metaseries['source'] = station_data['source']
            station_metaseries['type'] = station_data['type']
            station_metaseries['variables'] = station_data['variables']
            station_metaseries['units'] = station_data['units']
            station_metaseries['unit_type'] = ["Instantaneous"]
            station_metaseries['max_values'] = station_data['max_values']
            station_metaseries['min_values'] = station_data['min_values']
            station_metaseries['description'] = station_data['description']
            station_metaseries['run_name'] = station_data['run_name']
            station_metaseries['mean_sea_level'] = station_data['mean_sea_level']
            station_metaseries['min_wl'] = station_data['min_wl']
            station_metaseries['max_wl'] = station_data['max_wl']

            return station_metaseries
        else:
            logger_bulk.error("Requested db type - %s does not exit" % db_type)

    else:
        logger_bulk.error("Requested station type - %s does not exit" % station_type)



def add_station_curw_iot(db_type, action_type, station_type, data, logger_bulk):

    #backupfile name



    #logger_bulk.error(data)
    stations = CONFIG_curwiot_station['stations']
    data_curwiot = data

    #refer to the action type, if the action type not listed prompt an error
    if action_type == 'add_station':

        for station_data in data_curwiot:

            for station in stations:

                #check if the station already exist in the config file, if not add to the config
                if station['stationId'] == station_data['stationId']:
                    break
            else:
                curwiot_station_metaseries = get_station_metaseries(station_type, db_type, station_data, logger_bulk)
                CONFIG_curwiot_station['stations'].insert(-1, curwiot_station_metaseries)

                curwiot_updated = json.dumps(CONFIG_curwiot_station, sort_keys=True, indent=4)


                with open(pjoin(root_dir, '../config/StationConfig.json'), "w") as outfile:

                    #logger_bulk.error(outfile.write(curwiot_updated))
                    outfile.write(curwiot_updated)

    if action_type == 'remove_station':

        for station_data in data_curwiot:
            for i in range(len(stations)):
                if stations[i]['stationId'] == station_data['stationId']:
                    del stations[i]
                    break

            curwiot_updated = json.dumps(CONFIG_curwiot_station, sort_keys=True, indent=4)
            with open(pjoin(root_dir, '../config/StationConfig.json'), "w") as outfile:
                outfile.write(curwiot_updated)

def add_station_to_all(action_type, station_type, data, logger_bulk):
    backupfile = 'CONFIG.backup_%s.json' % date

    db_type1 = 'curw_iot'
    db_type2 = 'curw_obs'

    stations_curw = CONFIG_curw_station[station_type]
    data_curw = data
    stations_curwobs = CONFIG_curwobs_station[station_type]
    data_curwobs = data

    #First add station to the IoT config

    add_station_curw_iot(db_type1, action_type, station_type,  data, logger_bulk)

    #Refer to the action type, if the action type not listed prompt an error

    if action_type == 'add_station':

        #Secondly add station to the curw and then to curw obs config

        for station_data_curw in data_curw:
            for station_curw in stations_curw:
                #Check if station already exist in the config file, if not add to the config
                if station_curw['stationId'] == station_data_curw['stationId']:
                    break
            else:
                logger_bulk.error(pjoin(root_dir, '../../ExtractAndPush/CONFIG.dist.json'))
                # write a backupfile before dumping to the StationConfig.json
                with open(pjoin(root_dir, '../../ExtractAndPush/CONFIG.dist.json'), "r") as sta_config, \
                        open(pjoin(root_dir, '../../ExtractAndPush/Backup/backupfile'), "w+") as sta_backupconfig:
                    sta_backupconfig.write(sta_config.read())

                curw_station_metaseries = get_station_metaseries(station_type, db_type1, station_data_curw, logger_bulk)
                CONFIG_curw_station[station_type].insert(-1, curw_station_metaseries)

            curw_updated = json.dumps(CONFIG_curw_station, sort_keys=True, indent=4)

            with open(pjoin(root_dir, '../../ExtractAndPush/CONFIG.dist.json'), "w") as sta_configdist:
                sta_configdist.write(curw_updated)
                with open(pjoin(root_dir, '../../ExtractAndPush/CONFIG.json'), "w") as sta_config:
                    sta_config.write(sta_configdist.read())

        #Adding the station to the curwobs config
        for station_data_curwobs in data_curwobs:
            for station_curwobs in stations_curwobs:
                #Check if the station already exist in the config file, if not add to the config
                if station_curwobs['stationId'] == station_data_curwobs['stationId']:
                    break
            else:

                # write a backupfile before dumping to the StationConfig.json
                with open(pjoin(root_dir, '../../Data-Pusher-Obs/CONFIG.dist.json'), "r") as sta_config, \
                        open(pjoin(root_dir, '../../Data-Pusher-Obs/Backup/backupfile'),
                             "w+") as sta_backupconfig:
                    sta_backupconfig.write(sta_config.read())

                curwobs_station_metaseries = get_station_metaseries(station_type, db_type2, station_data_curwobs, logger_bulk)
                CONFIG_curwobs_station[station_type].insert(-1, curwobs_station_metaseries)

            curwobs_updated = json.dumps(CONFIG_curwobs_station, sort_keys=True, indent=4)
            with open(pjoin(root_dir, '../../Data-Pusher-Obs/CONFIG.dist.json'), "w") as outfile:
                outfile.write(curwobs_updated)

    if action_type == 'remove_station':
        #First Remove the station from curw and then from curwobs config
        for station_data_curw in data_curw:
            for i in range(len(stations_curw)):
                #Check if the station already exist in the config, if so remove it from the config
                if stations_curw[i]['stationId'] == station_data_curw['stationId']:
                    del stations_curw[i]
                    break

            curw_updated = json.dumps(CONFIG_curw_station, sort_keys=True, indent=4)
            with open(pjoin(root_dir, '../../ExtractAndPush/CONFIG.dist.json'), "w") as outfile:
                outfile.write(curw_updated)

        for station_data_curwobs in data_curwobs:
            for i in range(len(stations_curwobs)):
                if stations_curwobs[i]['stationId'] == station_data_curwobs['stationId']:
                    del stations_curwobs[i]
                    break

            curwobs_updated = json.dumps(CONFIG_curwobs_station, sort_keys=True, indent=4)

            with open(pjoin(root_dir, '../../Data-Pusher-Obs/CONFIG.dist.json'), "w") as outfile:
                outfile.write(curwobs_updated)



