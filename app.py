#!/usr/local/bin/python3

import os
import json
import logging
import copy
from logging.config import dictConfig
from os.path import join as pjoin
from datetime import datetime
from flask import Flask, request
from curwmysqladapter import MySQLAdapter, Station
from utils.UtilStation import get_station_hash_map, forward_to_weather_underground, forward_to_dialog_iot, add_station_curw_iot, add_station_to_all
from utils import UtilValidation, UtilTimeseries, Utils
from config import Constants
from route import api

app = Flask(__name__)

try:
    root_dir = os.path.dirname(os.path.realpath(__file__))
    config = json.loads(open(pjoin(root_dir, 'config/CONFIG.json')).read())

    # Initialize Logger
    logging_config = json.loads(open(pjoin(root_dir, 'config/LOGGING_CONFIG.json')).read())
    dictConfig(logging_config)
    logger_single = logging.getLogger('single')
    logger_bulk = logging.getLogger('bulk')
    logger_api = logging.getLogger('api')
    logger_warp10 = logging.getLogger('warp10')
    # logger.addHandler(logging.StreamHandler())

    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_DB = "curw"
    MYSQL_PASSWORD = ""

    if 'MYSQL_HOST' in config:
        MYSQL_HOST = config['MYSQL_HOST']
    if 'MYSQL_USER' in config:
        MYSQL_USER = config['MYSQL_USER']
    if 'MYSQL_DB' in config:
        MYSQL_DB = config['MYSQL_DB']
    if 'MYSQL_PASSWORD' in config:
        MYSQL_PASSWORD = config['MYSQL_PASSWORD']


    db_adapter = MySQLAdapter(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)
    # Get Station Data for Bulk Data Format
    STATION_CONFIG = pjoin(root_dir, 'config/StationConfig.json')
    CON_DATA = json.loads(open(STATION_CONFIG).read())
    stations_map = get_station_hash_map(CON_DATA['stations'])


    # Get Station Data for Single Upload Chinese weather stations
    STATION_CONFIG_WU = pjoin(root_dir, 'config/StationConfigWU.json')
    CON_WU_DATA = json.loads(open(STATION_CONFIG_WU).read())
    wu_stations_map = get_station_hash_map(CON_WU_DATA['stations'])

    # Create common format with None values
    script_path = os.path.dirname(os.path.realpath(__file__))
    common_format = json.loads(open(os.path.join(script_path, 'config/TimeStep.json')).read())
    for key in common_format:
        common_format[key] = None

except Exception as e:
    logging.error(e)


def validate_bulk_request():
    content = request.get_json(silent=True)
    if not isinstance(content, object) and not content and 'ID' in content:
        raise Exception("Invalid request. Abort ...")
    return content

def validate_addstation_request():
    config_add = json.loads(open(pjoin(root_dir, 'config/CONFIG.dist.json')).read())

    addStationUser = config_add['addStation_user']
    addStationPassword = config_add['addStation_pssword']


    content = request.get_json(silent=True)
    user = content['user']
    passwd = content['PASSWORD']

    if not isinstance(content, object) and not content and 'user' in content:
        raise Exception("Invalid request. Abort ...")

    if not (addStationUser == user):
        raise Exception("Unauthorized User! Abort ...")

    if addStationUser == user:
        if not (addStationPassword == passwd ):
            raise Exception("Invalid Password! Abort ...")

    return content


def validate_bulk_date(time_step):
    # Mapping Response to common format
    new_time_step = copy.deepcopy(common_format)
    is_utc_date_time = True

    # -- DateUTC
    if 'dateutc' in time_step:
        new_time_step['DateUTC'] = Utils.get_date_time_object(time_step['dateutc'], as_str=True)
        # -- Time
        sl_time = Utils.get_date_time_object(time_step['dateutc']) + Constants.SL_OFFSET
        new_time_step['Time'] = sl_time.strftime(Constants.DATE_TIME_FORMAT)
    # -- DateIST
    if 'dateist' in time_step:
        is_utc_date_time = False
        utc_time = Utils.get_date_time_object(time_step['dateist']) - Constants.SL_OFFSET
        new_time_step['DateUTC'] = utc_time.strftime(Constants.DATE_TIME_FORMAT)
        # -- Time
        new_time_step['Time'] = Utils.get_date_time_object(time_step['dateist'], as_str=True)
    if 'DateUTC' not in new_time_step:
        raise Exception("Unable to find dateutc or dateist field")
    return new_time_step, is_utc_date_time


#####################################################################
#                    BULK DATA  WeatherStation                      #
#####################################################################
@app.route('/weatherstation/updateweatherstation', methods=['POST'])
def update_weather_station():
    try:
        content = validate_bulk_request()
        logger_bulk.info("%s", json.dumps(content))
        # logger_bulk.info("Headers:: %s", json.dumps(request.headers))
    except Exception as json_error:
        logger_bulk.error(json_error)
        return "Bad Request", 400

    station = stations_map.get(content.get('ID'), None)
    if station is not None:
        data = content['data']
        if len(data) < 1:
            logger_bulk.error("Request does not have data")
            return "Request does not have any data", 404
        timeseries = []

        for time_step in data:
            try:
                new_time_step, is_utc_date_time = validate_bulk_date(time_step)
            except Exception as dateutc_error:
                logger_bulk.error('dateutc: %s', dateutc_error)
                return "Bad Request: " + str(dateutc_error), 400

            try:
                # -- TemperatureC
                if 'tempc' in time_step:
                    new_time_step['TemperatureC'] = float(time_step['tempc'])
            except Exception as tempc_error:
                logger_bulk.error('tempc: %s', tempc_error)
                return "Bad Request: Unable Validate tempc field value", 400
            try:
                # -- TemperatureF
                if 'tempf' in time_step:
                    new_time_step['TemperatureC'] = (float(time_step['tempf']) - 32) * 5 / 9
            except Exception as tempf_error:
                logger_bulk.error('tempf: %s', tempf_error)
                return "Bad Request: Unable to validate tempf field value", 400

            try:
                # -- PrecipitationMM
                if 'rainMM' in time_step:
                    new_time_step['PrecipitationMM'] = float(time_step['rainMM'])
            except Exception as rainMM_error:
                logger_bulk.error('rainMM: %s', rainMM_error)
                return "Bad Request: Unable to validate rainMM field value", 400
            try:
                # -- PrecipitationIn
                if 'rainin' in time_step:
                    new_time_step['PrecipitationMM'] = float(time_step['rainin']) * 25.4
            except Exception as rainin_error:
                logger_bulk.error('rainin: %s', rainin_error)
                return "Bad Request: Unable to validate rainin field value", 400

            try:
                # TODO: Handle dailyrainMM from rainMM separately
                # -- DailyPrecipitationMM
                if 'dailyrainMM' in time_step:
                    new_time_step['PrecipitationMM'] = float(time_step['dailyrainMM'])
            except Exception as dailyrainMM_error:
                logger_bulk.error('dailyrainMM: %s', dailyrainMM_error)
                return "Bad Request: Unable to validate dailyrainMM field value", 400
            try:
                # -- DailyPrecipitationIn
                if 'dailyrainin' in time_step:
                    new_time_step['PrecipitationMM'] = float(time_step['dailyrainin']) * 25.4
            except Exception as dailyrainin_error:
                logger_bulk.error('dailyrainin: %s', dailyrainin_error)
                return "Bad Request: Unable to validate dailyrainin field value", 400

            try:
                # -- Rain Ticks
                if 'rain' in time_step and isinstance(time_step['rain'], list):
                    new_ticks = []
                    # Convert all ticks into SL time
                    for tick in time_step['rain']:
                        new_ticks.append(Utils.get_date_time_object(tick) + Constants.SL_OFFSET
                                         if is_utc_date_time else Utils.get_date_time_object(tick, unix_offset=Constants.SL_OFFSET))
                    new_time_step['Ticks'] = new_ticks
            except Exception as rain_error:
                logger_bulk.error('rain: %s', rain_error)
                return "Bad Request: Unable to validate rain field list", 400

            try:
                # -- WindSpeedKMH
                if 'windspeedkmh' in time_step:
                    new_time_step['WindSpeedM/S'] = Utils.get_float(time_step['windspeedkmh'], 'windspeedkmh', logger_bulk) / 3.6
                # -- WindSpeedMPH
                if 'windspeedmph' in time_step:
                    new_time_step['WindSpeedM/S'] = Utils.get_float(time_step['windspeedmph'], 'windspeedmph', logger_bulk) * 1.609344 / 3.6
                # -- WindGustKMH
                if 'windgustkmh' in time_step:
                    new_time_step['WindGustM/S'] = Utils.get_float(time_step['windgustkmh'], 'windgustkmh', logger_bulk) / 3.6
                # -- WindGustMPH
                if 'windgustmph' in time_step:
                    new_time_step['WindGustM/S'] = Utils.get_float(time_step['windgustmph'], 'windgustmph', logger_bulk) * 1.609344 / 3.6
                # -- WindDirection
                if 'winddir' in time_step:
                    new_time_step['WindDirectionDegrees'] = Utils.get_float(time_step['winddir'], 'winddir', logger_bulk)

                # -- Humidity
                if 'humidity' in time_step:
                    new_time_step['Humidity'] = Utils.get_float(time_step['humidity'], 'humidity', logger_bulk)

                # -- SolarRadiation
                if 'solarradiation' in time_step:
                    new_time_step['SolarRadiationW/m2'] = Utils.get_float(time_step['solarradiation'], 'solarradiation', logger_bulk)

                # -- Pressure
                if 'baromMM' in time_step:
                    new_time_step['pressureBaromMM'] = Utils.get_float(time_step['baromMM'], 'baromMM', logger_bulk)
                    
            except Exception as error:
                logger_bulk.error(error)
                return "Bad Request: " + str(error), 400

            timeseries.append(new_time_step)

        save_timeseries(db_adapter, station, timeseries, logger_bulk)
        return "success"
    else:
        logger_bulk.warning("Unknown Station: %s", content.get('ID'))
        return "Failure", 404


#####################################################################
#                    BULK DATA  WaterLevelGauge                     #
#####################################################################
@app.route('/waterlevelgauge/updatewaterlevelgauge', methods=['POST'])
def update_waterlevel_guage():
    try:
        content = validate_bulk_request()
        logger_bulk.info("%s", json.dumps(content))
        # logger_bulk.info("Headers:: %s", json.dumps(request.headers))
    except Exception as json_error:
        logger_bulk.error(json_error)
        return "Bad Request", 400

    station = stations_map.get(content.get('ID'), None)
    if station is not None:
        data = content['data']
        if len(data) < 1:
            logger_bulk.error("Request does not have data")
            return "Request does not have any data", 404
        timeseries = []

        for time_step in data:
            try:
                new_time_step, is_utc_date_time = validate_bulk_date(time_step)
            except Exception as dateutc_error:
                logger_bulk.error('dateutc: %s', dateutc_error)
                return "Bad Request: " + str(dateutc_error), 400

            try:
                # -- WaterlevelM
                if 'waterlevelm' in time_step:
                    new_time_step['WaterlevelM'] = float(time_step['waterlevelm'])
            except Exception as waterlevelm_error:
                logger_bulk.error('waterlevelm : %s', waterlevelm_error)
                return "Bad Request: Unable Validate waterlevelm field value", 400

            timeseries.append(new_time_step)

        save_timeseries(db_adapter, station, timeseries, logger_bulk)
        return "success"
    else:
        logger_bulk.warning("Unknown Station: %s", content.get('ID'))
        return "Failure", 404


#####################################################################
#                    SINGLE DATA                                    #
#####################################################################
@app.route('/weatherstation/updateweatherstation.php', methods=['GET'])
def update_weather_station_single():
    try:
        data = request.args.to_dict()
        logger_single.info("%s", json.dumps(data))
        if not isinstance(data, dict) and not data and 'ID' in data:
            raise Exception("Invalid request. Abort ...")
    except Exception as json_error:
        logger_single.error(json_error)
        return "Bad Request", 400

    station = wu_stations_map.get(data.get('ID'), None)
    if station is not None:
        sl_time = datetime.strptime(data['dateutc'], Constants.DATE_TIME_FORMAT) + Constants.SL_OFFSET
        # Mapping Response to common format
        new_time_step = copy.deepcopy(common_format)

        try:
            # -- DateUTC
            if 'dateutc' in data:
                new_time_step['DateUTC'] = data['dateutc']
            # -- Time
            new_time_step['Time'] = sl_time.strftime(Constants.DATE_TIME_FORMAT)
        except Exception as dateutc_error:
            logger_single.error('dateutc: %s', dateutc_error)
            return "Bad Request: " + str(dateutc_error), 400

        try:
            # -- TemperatureC
            if 'tempc' in data:
                new_time_step['TemperatureC'] = Utils.get_float(data['tempc'], 'tempc', logger_single)
            # -- TemperatureF
            if 'tempf' in data:
                new_time_step['TemperatureC'] = (Utils.get_float(data['tempf'], 'tempf', logger_single) - 32) * 5 / 9

            # -- daily PrecipitationIn
            if 'dailyrainin' in data:
                new_time_step['PrecipitationMM'] = Utils.get_float(data['dailyrainin'], 'dailyrainin', logger_single) * 25.4

            # -- WindSpeedKMH
            if 'windspeedkmh' in data:
                new_time_step['WindSpeedM/S'] = Utils.get_float(data['windspeedkmh'], 'windspeedkmh', logger_single) / 3.6
            # -- WindSpeedMPH
            if 'windspeedmph' in data:
                new_time_step['WindSpeedM/S'] = Utils.get_float(data['windspeedmph'], 'windspeedmph', logger_single) * 1.609344 / 3.6
            # -- WindGustKMH
            if 'windgustkmh' in data:
                new_time_step['WindGustM/S'] = Utils.get_float(data['windgustkmh'], 'windgustkmh', logger_single) / 3.6
            # -- WindGustMPH
            if 'windgustmph' in data:
                new_time_step['WindGustM/S'] = Utils.get_float(data['windgustmph'], 'windgustmph', logger_single) * 1.609344 / 3.6
            # -- WindDirection
            if 'winddir' in data:
                new_time_step['WindDirectionDegrees'] = Utils.get_float(data['winddir'], 'winddir', logger_single)

            # -- Humidity
            if 'humidity' in data:
                new_time_step['Humidity'] = Utils.get_float(data['humidity'], 'humidity', logger_single)

            # -- SolarRadiation
            if 'solarradiation' in data:
                new_time_step['SolarRadiationW/m2'] = Utils.get_float(data['solarradiation'], 'solarradiation', logger_single)
        except Exception as error:
            logger_single.error(error)
            return "Bad Request: " + str(error), 400

        save_timeseries(db_adapter, station, [new_time_step], logger_single)
        if 'wunderground' in station:
            wu_data = copy.deepcopy(data)
            wu_data['ID'] = station['wunderground']['stationId']
            wu_data['PASSWORD'] = station['wunderground']['password']
            forward_to_weather_underground(wu_data, logger_single)
        if 'dialog' in station:
            dialog_data = copy.deepcopy(data)
            dialog_data['ID'] = station['dialog']['stationId']
            dialog_data['PASSWORD'] = station['dialog']['password']
            forward_to_dialog_iot(dialog_data, logger_single)

        return "success"
    else:
        logger_single.warning("Unknown Station: %s", data.get('ID'))
        return "Failure", 404


def save_timeseries(adapter, station, timeseries, logger):
    force_insert = True
    meta_data = {
        'station': 'Hanwella',
        'variable': 'Precipitation',
        'unit': 'mm',
        'type': 'Observed',
        'source': 'WeatherStation',
        'name': 'WUnderground',
    }

    logger.debug('\n**************** STATION **************')
    logger.debug('station name: %s, run_name: %s', station['name'], station['run_name'])
    #  Check whether station exists
    is_station_exists = adapter.get_station({'name': station['name'], 'stationId': station['stationId']})
    if is_station_exists is None:
        logger.warning('Station %s does not exists.', station['name'])
        if 'station_meta' in station:
            station_meta = station['station_meta']
            station_meta.insert(0, Station.CUrW)
            row_count = adapter.create_station(station_meta)
            if row_count > 0:
                logger.warning('Created new station %s', station_meta)
            else:
                logger.error("Unable to create station %s", station_meta)
                return
        else:
            logger.error("Could not find station meta data to create new ", station['name'])
            return

    if len(timeseries) < 1:
        logger.error('INFO: Timeseries does not have any data : %s', timeseries)
        return

    logger.debug('Start Date : %s', timeseries[0]['Time'])
    logger.debug('End Date : %s', timeseries[-1]['Time'])
    start_date_time = datetime.strptime(timeseries[0]['Time'], '%Y-%m-%d %H:%M:%S')
    end_date_time = datetime.strptime(timeseries[-1]['Time'], '%Y-%m-%d %H:%M:%S')

    meta = copy.deepcopy(meta_data)
    meta['station'] = station['name']
    meta['start_date'] = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    meta['end_date'] = end_date_time.strftime("%Y-%m-%d %H:%M:%S")

    variables = station['variables']
    units = station['units']
    if 'run_name' in station:
        meta['name'] = station['run_name']
    for i in range(0, len(variables)):
        extracted_timeseries = UtilTimeseries.extract_single_variable_timeseries(timeseries, variables[i], station['stationId'])

        if len(extracted_timeseries) < 1:
            logger.debug('Timeseries of variable:%s does not have data. Skip ...', variables[i])
            continue

        meta['variable'] = variables[i]
        meta['unit'] = units[i]
        event_id = adapter.get_event_id(meta)
        if event_id is None:
            event_id = adapter.create_event_id(meta)
            logger.debug('HASH SHA256 created: %s', event_id)
        else:
            logger.debug('HASH SHA256 exists: %s', event_id)
            meta_query = copy.deepcopy(meta_data)
            meta_query['station'] = station['name']
            meta_query['variable'] = variables[i]
            meta_query['unit'] = units[i]
            if 'run_name' in station:
                meta_query['name'] = station['run_name']
            query_opts = {
                'from': start_date_time.strftime("%Y-%m-%d %H:%M:%S"),
                'to': end_date_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            existing_timeseries = adapter.retrieve_timeseries(meta_query, query_opts)
            if not isinstance(existing_timeseries, list):
                logger.error('Timeseries must be a list.\n', meta_query, query_opts)
            elif len(existing_timeseries) > 0 and len(existing_timeseries[0]['timeseries']) > 0 and not force_insert:
                logger.warning('Timeseries already exists. Use force insert to insert data.\n')
                continue

        validation_obj = {
            'max_value': station['max_values'][i],
            'min_value': station['min_values'][i],
        }
        extracted_timeseries = UtilValidation.handle_duplicate_values(extracted_timeseries, validation_obj)

        for l in extracted_timeseries[:3] + extracted_timeseries[-2:]:
            logger.debug(l)

        row_count = adapter.insert_timeseries(event_id, extracted_timeseries, force_insert)
        logger.debug('%s rows inserted.\n' % row_count)


#####################################################################
#                    Edit Station                                   #
#####################################################################
@app.route('/weatherstation/editstation', methods=['POST'])
def add_weather_station():
    try:
        content = validate_addstation_request()
        logger_bulk.info("%s", json.dumps(content))
        # logger_bulk.info("Headers:: %s", json.dumps(request.headers))
    except Exception as json_error:
        logger_bulk.error(json_error)
        return "Bad Request", 400

    db_type = content.get('db type')


    if db_type is not None:
        data = content['data']
        action_type = content.get('action type')
        station_type = content.get('station type')
        db_type = content.get('db type')

        logger_bulk.error(action_type)
        logger_bulk.error(station_type)
        logger_bulk.error(data)

        if data is not None:
            if db_type == 'curw_iot':
                logger_bulk.error("**************")
                logger_bulk.error(action_type)
                logger_bulk.error(station_type)
                logger_bulk.error(data)

                #add curw station only to the curw_iot
                try:
                    add_station_curw_iot(db_type, action_type, station_type, data, logger_bulk)
                    
                except Exception as json_error:
                    logger_bulk.error(json_error)
                    return "The changes did not apply to curw_iot platform", 400



            elif db_type == 'curw_all':
                #first add the station to curw_iot and then to other two
                try:
                    add_station_to_all(action_type, station_type, data, logger_bulk)
                    return "Success", 200
                except Exception as json_error:
                    logger_bulk.error(json_error)
                    return "The changes did not apply to curw_iot platform", 400



            else:
                return "Unknown Action type, Failure", 404
    else:
        return "Bad Request, No action type stated", 400

@app.route('/')
def index():
    return "Welcome to CUrW !"


app.register_blueprint(api.output_api)


if __name__ == '__main__':
    app.run(debug=True)
