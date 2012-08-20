# -*- coding: utf-8 -*-

''' Usage:
cons_key = 'warehouse'
cons_secret = 'lerolero'

consumer = oauth2.Consumer(key=cons_key, secret=cons_secret)
url = 'http://localhost:8000/accounting/inventory'

api = RemoteJSONResource(url, cons_key, cons_secret)

api.get('/product')
'''

import urllib
import urllib2
import httplib

import oauth2  # third party lib
from django.utils import simplejson


class BaseRemoteResource(object):
    consumer = None
    client = None

    def __init__(self, base_url='', consumer_key='', consumer_secret=''):
        self.base_url = base_url
        self.get_consumer(consumer_key, consumer_secret)

    def get_consumer(self, key='', secret=''):
        ''' build a consumer to sign the request'''
        if self.consumer:
            return self.consumer

        self.consumer = oauth2.Consumer(key=key, secret=secret)
        return self.consumer

    def get_client(self):
        '''build a client to do signed requests'''
        if self.client:
            return self.client
        self.client = oauth2.Client(self.get_consumer())
        return self.client

    def prepare_data(self, data):
        ''' data as a dict'''
        if data is not None:
            data = urllib.urlencode(data)
        else:
            data = ''
        return data

    def prepare_url(self, path, data=None):
        ''' Put the base_pat and path together

        If data is provided, it put as GET data in url
        '''

        url = self.base_url
        if not (self.base_url.endswith('/') or path.startswith('/')):
            url += '/'
        url += path

        if data is not None:
            data = urllib.urlencode(data)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += data

        return url

    def request(self, *args, **kwargs):
        ''' Wraps the request of the Resource
        Useful to do a new type of request'''
        return self._request(*args, **kwargs)

    def _request(self, uri, method='GET', *args, **kwargs):
        ''' Make a request and handle the return code.
        Only accept 2XX HTTP Codes'''

        client = self.get_client()
        client.disable_ssl_certificate_validation = True
        response, content = client.request(uri, method=method, *args, **kwargs)
        if not response['status'].startswith('2'):
            status = int(response['status'])
            msg = "Request %s '%s' failed as (%s - %s)" % (method, uri, status, httplib.responses[status])
            raise urllib2.HTTPError(uri, int(response['status']), msg, response, None)
        return response, content

    def submit(self, method='POST', path='', data=None):
        ''' Submit data in body part, used by POST and PUT methods'''
        data = self.prepare_data(data)
        url = self.prepare_url(path)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        return self.request(uri=url, method=method.upper(),
                            body=data, headers=headers)

    def post(self, path='', data=None):
        ''' data as a dict'''
        return self.submit('POST', path, data)

    def put(self, path='', data=None):
        return self.submit('PUT', path, data)



class RemoteJSONResource(BaseRemoteResource):

    def request(self, *args, **kwargs):
        ''' Wraps the request of the Resource
        Useful to do a new type of request'''
        return self._json_request(*args, **kwargs)

    def _json_request(self, *args, **kwargs):
        ''' Make a request and decode the json body'''

        resp, content = self._request(*args, **kwargs)
        json_data = ''
        if content:
            json_data = simplejson.loads(content)
        return json_data

    def prepare_data(self, data):
        ''' data as a dict'''
        if data is not None:
            # Due to a instruction on OAuth Protocol
            # http://oauth.net/core/1.0/#signing_process
            # http://stackoverflow.com/questions/3587454/oauth-posting-json
            # We can't use the Piston feature to decode the JSON body automatically for us
            # So, we just POST the json as field called 'data'
            # If we put the body as a plain JSON and declare the content-type header as 'application/json'
            # the OAuth signature will fail
            data = simplejson.dumps(data)
            data = urllib.urlencode({'data': data})
        else:
            data = ''
        return data


    def get(self, path='', data=None):
        headers = {'Content-Type': 'application/json'}
        url = self.prepare_url(path, data)

        return self.request(uri=url, method='GET', headers=headers)
