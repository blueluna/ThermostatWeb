# Create your views here.

from datetime import datetime, timedelta
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from jsonrpc import jsonrpc_method
from jsonrpc.exceptions import Error, InvalidRequestError, InvalidParamsError

from thermostat.models import ThermostatDevice, TemperatureDevice, Temperature, ThermostatState, ThermostatConfiguration
from .iso8601 import parse_date, ParseError

class ThermostatDeviceNotFound(Error):
    code = -1001
    message = 'Thermostat device not found.'
    status = 200

class TemperatureDeviceNotFound(Error):
    code = -1002
    message = 'Temperature device not found.'
    status = 200

class ThermostatConfigurationNotFound(Error):
    code = -1003
    message = 'Thermostat configuration not found.'
    status = 200

class ThermostatStateNotFound(Error):
    code = -1004
    message = 'Thermostat state not found.'
    status = 200

def rpc_parse_datetime(isodate):
    try:
        dt = parse_date(isodate)
        return dt
    except ParseError:
        raise InvalidParamsError("Invalid datetime.")

def rpc_parse_datetime_range(range_from=None, range_to=None):
    if range_to is None:
        dt_to = datetime.utcnow()
        dt_to = dt_to.replace(second=0, microsecond=0) # use minute resolution
        dt_to = dt_to + timedelta(minutes=1) # round up
    else:
        try:
            dt_to = parse_date(range_to)
        except ParseError:
            raise InvalidParamsError("Invalid range_to date.")
    if range_from is None:
        dt_from = dt_to - timedelta(days=1)
    else:
        try:
            dt_from = parse_date(range_from)
        except ParseError:
            raise InvalidParamsError("Invalid range_from date.")
    return (dt_from, dt_to)

def valid_1wire_id(deviceId):
    return True

@jsonrpc_method('thermostat.temperature.add(deviceId=String, datetime=String, value=Number) -> Object')
def rpc_temperature_add(request, deviceId, datetime, value):
    try:
        device = TemperatureDevice.objects.get(deviceId=deviceId)
    except ObjectDoesNotExist:
        if valid_1wire_id(deviceId):
            device = TemperatureDevice(deviceId=deviceId, name=deviceId, thermostat=0)
            device.save()
        else:
            raise TemperatureDeviceNotFound()
    if device:
        dt = parse_date(datetime)
        temp = Temperature(device=device, datetime=dt, value=value)
        temp.save()
        return {"result": "OK", "datetime": dt.isoformat(), "value": value} 
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.set_state(device=Number, datetime=String, state=Number) -> String')
def rpc_thermostat_set_state(request, device, datetime, state):
    try:
        thermostat = ThermostatDevice.objects.get(id=device)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        if state == 0:
            enabled = False
        elif state == 1:
            enabled = True
        else:
            raise InvalidParamsError("Invalid state.")
        try:
            dbState = ThermostatState.objects.filter(device=thermostat).order_by('-datetime')[0]
        except Exception:
            dbState = None
        if dbState is None or dbState.enabled != enabled:
            dt = parse_date(datetime)
            state = ThermostatState(device=thermostat, datetime=dt, enabled=enabled)
            state.save()
            return "OK"
        return "UNCHANGED"
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.get_state(device=Number) -> Object')
def rpc_thermostat_get_state(request, device):
    try:
        thermostat = ThermostatDevice.objects.get(id=device)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        try:
            state = ThermostatState.objects.filter(device=thermostat).order_by('-datetime')[0]
            return {
                'datetime': state.datetime.isoformat(),
                'state': state.enabled 
                }
        except Exception:
            raise ThermostatStateNotFound()
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.get_states_range(device=Number, range_to=String, range_from=String) -> Object')
def rpc_thermostat_get_states_range(request, device, range_to=None, range_from=None):
    (dt_from, dt_to) = rpc_parse_datetime_range(range_from, range_to)
    try:
        thermostat = ThermostatDevice.objects.get(id=device)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        try:
            states = ThermostatState.objects.filter(device=thermostat) \
                .filter(datetime__range=(dt_from, dt_to)) \
                .order_by('-datetime')[:288]
            if len(states) == 0:
                try:
                    state = ThermostatState.objects.filter(device=thermostat).order_by('-datetime')[0]
                    states = [state]
                except Exception:
                    pass
            elif len(states) == 1:
                try:
                    states = ThermostatState.objects.filter(device=thermostat).order_by('-datetime')[:2]
                    states = [state]
                except Exception:
                    pass                
        except Exception:
            raise ThermostatStateNotFound()
        result = []
        if len(states) > 0:
            reorder = {}
            for state in states:
                reorder[state.datetime] = state.enabled
            keys = sorted(reorder.keys())
            value = 1 if reorder[keys[0]] else 0
            result.append({'datetime': dt_from.isoformat(), 'value': value })
            for key in keys:
                if key < dt_from:
                    continue
                value = 1 if reorder[key] else 0
                result.append({'datetime': key.isoformat(), 'value': value})
            result.append({'datetime': dt_to.isoformat(), 'value': value })
        return {'device': thermostat.id, 'states': result, 'from': dt_from.isoformat(), 'to': dt_to.isoformat()}
    raise TemperatureDeviceNotFound()


@jsonrpc_method('thermostat.set_configuration(device=Number, datetime=String, mode=Number, normalThreshold=Number, lowThreshold=Number) -> String')
def rpc_thermostat_set_configuration(request, device, datetime, mode, thresholdNormal, thresholdLow):
    try:
        thermostat = ThermostatDevice.objects.get(id=device)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        try:
            configuration = ThermostatConfiguration.objects.filter(device=thermostat).order_by('-datetime')[0]
        except Exception:
            configuration = None
        dt = rpc_parse_datetime(datetime)
        replace = False
        if configuration is None:
            replace = True
        else:
            if int(mode) != int(configuration.mode):
                replace = True
            if thresholdNormal != configuration.thresholdNormal:
                replace = True
            if thresholdLow != configuration.thresholdLow:
                replace = True
        if replace:
            cfg = ThermostatConfiguration(
                device=thermostat, datetime=dt, mode=mode,
                thresholdNormal=thresholdNormal,
                thresholdLow=thresholdLow
                )
            cfg.save()
            return "OK"
        return "UNCHANGED"
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.get_configuration(device=Number) -> Object')
def rpc_thermostat_get_configuration(request, device):
    try:
        thermostat = ThermostatDevice.objects.get(id=device)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        try:
            configuration = ThermostatConfiguration.objects.filter(device=thermostat).order_by('-datetime')[0]
            cfg = {
                'datetime': configuration.datetime.isoformat(),
                'mode': configuration.mode,
                'thresholdNormal': configuration.thresholdNormal,
                'thresholdLow': configuration.thresholdLow
                }
            return cfg
        except Exception:
            raise ThermostatConfigurationNotFound()
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.list() -> Object')
def rpc_thermostat_list(request):
    devices = ThermostatDevice.objects.all()
    devs = {}
    for device in devices:
        devs[device.id] = device.name
    return devs

@jsonrpc_method('thermostat.temperature.list(thermostatId=Number) -> Object')
def rpc_temperature_list(request, thermostatId):
    try:
        thermostat = ThermostatDevice.objects.get(id=thermostatId)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        result = []
        devices = TemperatureDevice.objects.filter(thermostat=thermostat.id)
        for device in devices:
            result.append({'id': device.deviceId, 'name': device.name})
        return result
    raise ThermostatDeviceNotFound()

@jsonrpc_method('thermostat.temperature.get_range(deviceId=Number, range_to=String, range_from=String) -> Object')
def rpc_temperatures_get_range(request, deviceId, range_to=None, range_from=None):
    (dt_from, dt_to) = rpc_parse_datetime_range(range_from, range_to)
    try:
        temperature = TemperatureDevice.objects.get(deviceId=deviceId)
    except ObjectDoesNotExist:
        temperature = None
    if temperature:
        temperatures = Temperature.objects \
            .filter(device=temperature.id) \
            .filter(datetime__range=(dt_from, dt_to)) \
            .order_by('-datetime')[:288]
        temps = []
        for temperature in temperatures:
            temps.append({'datetime': temperature.datetime.isoformat(), 'value': temperature.value})
        return {'device': deviceId, 'temperatures': temps, 'from': dt_from.isoformat(), 'to': dt_to.isoformat()}
    raise TemperatureDeviceNotFound()

def index(request):
    devices = ThermostatDevice.objects.all()
    return render(request, 'index.html', {'devices': devices})

def thermostat(request, id):
    try:
        thermostat = ThermostatDevice.objects.get(id=id)
    except ObjectDoesNotExist:
        thermostat = None
    tempDevices = None
    if thermostat:
        tempDevices = TemperatureDevice.objects.filter(thermostat=thermostat.id)
        return render(request, 'thermostat.html', {'id': id, 'name': thermostat.name, 'tempDevices': tempDevices})
    else:
        return render(request, 'thermostat.html')

def thermostat_temperature(request, thermostatId, temperatureId):
    try:
        thermostat = ThermostatDevice.objects.get(id=thermostatId)
    except ObjectDoesNotExist:
        thermostat = None
    if thermostat:
        try:
            temperature = TemperatureDevice.objects.get(deviceId=temperatureId)
        except ObjectDoesNotExist:
            temperature = None
    if thermostat and temperature:
        return render(request, 'temperature.html', {'thermostatId': thermostat.id, 'temperatureId': temperature.deviceId, 'name': temperature.name})
    else:
        return render(request, 'temperature.html')
