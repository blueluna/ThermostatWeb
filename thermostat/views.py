# Create your views here.

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from jsonrpc import jsonrpc_method
from jsonrpc.exceptions import Error, InvalidRequestError

from thermostat.models import ThermostatDevice, TemperatureDevice, Temperature

class ThermostatDeviceNotFound(Error):
    code = -1
    message = 'Thermostat device not found.'
    status = 200

class TemperatureDeviceNotFound(Error):
    code = -2
    message = 'Temperature device not found.'
    status = 200

@jsonrpc_method('thermostat.temperature.add(deviceId=String, datetime=String, value=Number) -> Object')
def rpc_temperature_add(request, deviceId, datetime, value):
    try:
        device = TemperatureDevice.objects.get(deviceId=deviceId)
    except ObjectDoesNotExist:
        raise TemperatureDeviceNotFound()
    if device:
        temp = Temperature(device=device, datetime=datetime, value=value)
        temp.save()
        return {}
    raise TemperatureDeviceNotFound()

@jsonrpc_method('thermostat.list() -> Object')
def rpc_thermostat_list(request):
    devices = ThermostatDevice.objects.all()
    result = {}
    for device in devices:
        result[device.name] = device.id
    return {'devices': result}

@jsonrpc_method('thermostat.temperature.list(thermostatId=Number) -> Object')
def rpc_temperature_list(request, thermostatId):
    try:
        thermostat = ThermostatDevice.objects.get(id=thermostatId)
    except ObjectDoesNotExist:
        raise ThermostatDeviceNotFound()
    if thermostat:
        result = {}
        devices = TemperatureDevice.objects.filter(thermostat=thermostat.id)
        for device in devices:
            result[device.deviceId] = device.name
        return {'devices': result}
    raise ThermostatDeviceNotFound()

@jsonrpc_method('thermostat.temperature.now(deviceId=Number) -> Object')
def rpc_temperatures_now(request, deviceId):
    try:
        temperature = TemperatureDevice.objects.get(deviceId=deviceId)
    except ObjectDoesNotExist:
        temperature = None
    if temperature:
        temperatures = Temperature.objects.filter(device=temperature.id).order_by('-datetime')[:240]
        temps = []
        for temperature in temperatures:
            temps.append({'datetime': temperature.datetime.isoformat(), 'value': temperature.value})
        return {'device': deviceId, 'temperatures': temps}
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
    return render(request, 'thermostat.html', {'tempDevices': tempDevices})

def temperature(request, id):
    try:
        temperature = TemperatureDevice.objects.get(deviceId=id)
    except ObjectDoesNotExist:
        temperature = None
    temperatures = None
    if temperature:
        temperatures = Temperature.objects.filter(device=temperature.id).order_by('-datetime')[:30]
    return render(request, 'temperature.html', {'device': id, 'temperatures': temperatures})
