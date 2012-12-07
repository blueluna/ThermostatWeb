/* Thermostat API
 * Copyright (c) 2012 Erik Svensson <erik.public@gmail.com>
 * Licensed under the MIT license.
 * Requires Mootools
 */

function ThermostatAPI(api_url)
{
    this._api_url = api_url;
    this._callback = function(id, response){};
    this._errback = function(id, status, error){};
    
    this.registerCallback = function(callback)
    {
        this._callback = callback;    
    };
    this.registerErrback = function(errback)
    {
        this._errback = errback;    
    };

    this.query = function(method, params, id, callback, errback)
    {
        if (callback == null) {
            callback = this._callback;    
        }
        if (errback == null) {
            errback = this._errback;
        }
        if (id == null) {
            id = 0
        }
        var query = {'jsonrpc': '2.0', 'id': id, 'method': method, 'params': params}
        var request = new Request.JSON({
            url: this._api_url,
            urlEncoded: false,
            headers: {'content-type': "application/json; charset=utf-8"},
            onError: function(text, error) { errback(id, -1, error); },
            onFailure: function(xhr) { errback(id, xhr.status, xhr.statusText); },
            onComplete: function(object) { if (object.error != null) { errback(object.id, object.error.code, object.error.message); } else { callback(object.id, object.result) } },
            data: JSON.encode(query)
        }).send();
    };
};
