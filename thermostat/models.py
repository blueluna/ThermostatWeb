from django.db import models

THERMOSTAT_NORMAL = 0
THERMOSTAT_LOW = 1

THERMOSTAT_MODE = (
    (THERMOSTAT_NORMAL, 'Normal'),
    (THERMOSTAT_LOW, 'Low'),
    )

class ThermostatDevice(models.Model):
    name = models.CharField(max_length=128)

class TemperatureDevice(models.Model):
    name = models.CharField(max_length=128)
    deviceId = models.CharField(max_length=32)
    thermostat = models.ForeignKey(ThermostatDevice)

class Temperature(models.Model):
    device = models.ForeignKey(TemperatureDevice)
    value = models.FloatField()
    datetime = models.DateTimeField()

class ThermostatState(models.Model):
    device = models.ForeignKey(ThermostatDevice)
    enabled = models.BooleanField()
    datetime = models.DateTimeField()

class ThermostatConfiguration(models.Model):
    device = models.ForeignKey(ThermostatDevice)
    mode = models.IntegerField(choices=THERMOSTAT_MODE, default=THERMOSTAT_NORMAL)
    thresholdNormal = models.FloatField()
    thresholdLow = models.FloatField()
    datetime = models.DateTimeField()
