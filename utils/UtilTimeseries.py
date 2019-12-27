from utils import UtilAlertEmail
def extract_single_variable_timeseries(timeseries, variable, stationname, opts=None):
    """
    Then Lines follows the data. This function will extract the given variable timeseries
    """
    if opts is None:
        opts = {}

    def precipitation(my_timeseries):
        print('Precipitation:: PrecipitationMM')
        new_timeseries = []
        for t in my_timeseries:
            if t['PrecipitationMM'] is not None:
                new_timeseries.append([t['Time'], t['PrecipitationMM']])

            if t['PrecipitationMM'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'Precipitation', t['PrecipitationMM'], t['Time'])
        return new_timeseries

    def daily_precipitation(my_timeseries):
        # TODO: Handle rainMM and dailyrainMM separately
        print('Precipitation:: DailyPrecipitationMM')
        new_timeseries = []
        for t in my_timeseries:
            if t['DailyPrecipitationMM'] is not None:
                new_timeseries.append([t['Time'], t['DailyPrecipitationMM']])
        return new_timeseries

    def ticks(my_timeseries):
        # HACK
        print('Tick:: Ticks')
        new_timeseries = []
        for t in my_timeseries:
            if t['Ticks'] is not None:
                for tick in t['Ticks']:
                    new_timeseries.append([tick, 1])
        return new_timeseries

    def temperature(my_timeseries):
        print('Temperature:: TemperatureC')
        new_timeseries = []
        for t in my_timeseries:
            if t['TemperatureC'] is not None:
                new_timeseries.append([t['Time'], t['TemperatureC']])

            if t['TemperatureC'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'Temperature', t['TemperatureC'], t['Time'])
        return new_timeseries

    def wind_speed(my_timeseries):
        print('WindSpeed:: WindSpeedM/S')
        new_timeseries = []
        for t in my_timeseries:
            if t['WindSpeedM/S'] is not None:
                new_timeseries.append([t['Time'], t['WindSpeedM/S']])

            if t['WindSpeedM/S'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'WindSpeed', t['WindSpeedM/S'], t['Time'])
        return new_timeseries

    def wind_gust(my_timeseries):
        print('WindGust:: WindGustM/S')
        new_timeseries = []
        for t in my_timeseries:
            if t['WindGustM/S'] is not None:
                new_timeseries.append([t['Time'], t['WindGustM/S']])
        return new_timeseries

    def wind_direction(my_timeseries):
        print('WindDirection:: WindDirectionDegrees')
        new_timeseries = []
        for t in my_timeseries:
            if t['WindDirectionDegrees'] is not None:
                new_timeseries.append([t['Time'], t['WindDirectionDegrees']])

            if t['WindDirectionDegrees'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'Wind Direction', t['WindDirectionDegrees'], t['Time'])
        return new_timeseries

    def humidity(my_timeseries):
        print('Humidity:: Humidity')
        new_timeseries = []
        for t in my_timeseries:
            if t['Humidity'] is not None:
                new_timeseries.append([t['Time'], t['Humidity']])

            if t['Humidity'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'Humidity', t['Humidity'], t['Time'])
        return new_timeseries

    def solar_radiation(my_timeseries):
        print('SolarRadiation:: SolarRadiationW/m2')
        new_timeseries = []
        for t in my_timeseries:
            if t['SolarRadiationW/m2'] is not None:
                new_timeseries.append([t['Time'], t['SolarRadiationW/m2']])
        return new_timeseries

    def pressure(my_timeseries):
        print('Pressure:: pressureBaromMM')
        new_timeseries = []
        for t in my_timeseries:
            if t['pressureBaromMM'] is not None:
                new_timeseries.append([t['Time'], t['pressureBaromMM']])

            if t['pressureBaromMM'] < 0:
                UtilAlertEmail.send_email('CUrW Alert', stationname, 'Air Pressure', t['pressureBaromMM'], t['Time'])
        return new_timeseries

    def waterlevel(my_timeseries):
        print('WaterLevel:: WaterlevelM')
        new_timeseries = []
        for t in my_timeseries:
            if t['WaterlevelM'] is not None:
                new_timeseries.append([t['Time'], t['WaterlevelM']])
        return new_timeseries

    def default(my_timeseries):
        print('default', my_timeseries)
        return []

    variable_dict = {
        'Precipitation': precipitation,
        'DailyPrecipitation': daily_precipitation,
        'Tick': ticks,
        'Temperature': temperature,
        'WindSpeed': wind_speed,
        'WindGust': wind_gust,
        'WindDirection': wind_direction,
        'Humidity': humidity,
        'SolarRadiation': solar_radiation,
        'Pressure': pressure,
        'Waterlevel': waterlevel
    }
    return variable_dict.get(variable, default)(timeseries)
    # --END extract_single_variable_timeseries --
