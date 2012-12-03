from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from jsonrpc import jsonrpc_site

from thermostat import views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.index, name='index'),
    url(r'^thermostat/(?P<id>\d+)/$', views.thermostat, name='index'),
    url(r'^temperature/(?P<id>[0-9A-F-a-f]+)/$', views.temperature, name='index'),

    # url(r'^ThermostatWeb/', include('ThermostatWeb.foo.urls')),
    url(r'^json/browse/', 'jsonrpc.views.browse', name="jsonrpc_browser"), # for the graphical browser/web console only, omissible
    url(r'^json/$', jsonrpc_site.dispatch, name='jsonrpc_mountpoint'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
