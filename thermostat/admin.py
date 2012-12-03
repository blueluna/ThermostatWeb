from django.contrib import admin
from thermostat.models import ThermostatDevice, TemperatureDevice

admin.site.register(ThermostatDevice)
admin.site.register(TemperatureDevice)
