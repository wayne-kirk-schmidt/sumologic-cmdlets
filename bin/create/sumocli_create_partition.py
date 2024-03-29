#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: create_connection a sumocli cmdlet creating connection

Usage:
   $ python  create_connection [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_create_connection
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   Apache 2.0
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

### beginning ###
import ast
import json
import os
import sys
import argparse
import http
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
create_connection is a Sumo Logic cli cmdlet creating a connection
""")


PARSER.add_argument("-a", metavar='<secret>', dest='MY_SECRET', \
                    help="set api (format: <key>:<secret>) ")
PARSER.add_argument("-k", metavar='<client>', dest='MY_CLIENT', \
                    help="set key (format: <site>_<orgid>) ")
PARSER.add_argument("-e", metavar='<endpoint>', dest='MY_ENDPOINT', \
                    help="set endpoint (format: <endpoint>) ")
PARSER.add_argument("-m", default=0, metavar='<myselfid>', \
                    dest='myselfid', help="provide specific id to lookup")
PARSER.add_argument("-p", default=0, metavar='<parentid>', \
                    dest='parentid', help="provide parent id to locate with")
PARSER.add_argument("-f", metavar='<outputfile>', default="stdout", dest='outputfile', \
                    help="Specify output format (default = stdout )")
PARSER.add_argument("-j", metavar='<jsonfile>', \
                    dest='jsonfile', help="specify the json payload")
PARSER.add_argument("-o", metavar='<overrides>', action='append', \
                    dest='overrides', help="specify override (format: key=value )")
PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='verbose', help="Increase verbosity")

ARGS = PARSER.parse_args()

if ARGS.MY_SECRET:
    (MY_APINAME, MY_APISECRET) = ARGS.MY_SECRET.split(':')
    os.environ['SUMO_UID'] = MY_APINAME
    os.environ['SUMO_KEY'] = MY_APISECRET

if ARGS.MY_CLIENT:
    (MY_DEPLOYMENT, MY_ORGID) = ARGS.MY_CLIENT.split('_')
    os.environ['SUMO_LOC'] = MY_DEPLOYMENT
    os.environ['SUMO_ORG'] = MY_ORGID
    os.environ['SUMO_TAG'] = ARGS.MY_CLIENT

if ARGS.MY_ENDPOINT:
    os.environ['SUMO_END'] = ARGS.MY_ENDPOINT
else:
    os.environ['SUMO_END'] = os.environ['SUMO_LOC']

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_LOC = os.environ['SUMO_LOC']
    SUMO_ORG = os.environ['SUMO_ORG']
except KeyError as myerror:
    print(f'Environment Variable Not Set :: {myerror.args[0]}')

### beginning ###
def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    source = SumoApiClient(SUMO_UID, SUMO_KEY)
    run_sumo_cmdlet(source)

def run_sumo_cmdlet(source):
    """
    This will collect the information on object for sumologic and then collect that into a list.
    the output of the action will provide a tuple of the orgid, objecttype, and id
    """
    target_object = "connection"
    target_dict = {}
    target_dict["orgid"] = SUMO_ORG
    target_dict[target_object] = {}

########

    jsonpayload = {
        "type": "string",
        "name": "string",
        "description": "",
        "url": "https://www.google.com",
        "headers": [ ],
        "customHeaders": [ ],
        "defaultPayload": "{ }",
        "webhookType": "Webhook",
    }
    src_items = source.create_connection(jsonpayload)
    target_id = src_items['id']

    src_item = source.get_fer(target_id)
    if str(src_item['id']) == str(target_id):
        target_dict[src_item['id']] = {}
        target_dict[src_item['id']].update({'parent' : SUMO_ORG})
        target_dict[src_item['id']].update({'id' : src_item['id']})
        target_dict[src_item['id']].update({'name' : src_item['name']})
        target_dict[src_item['id']].update({'dump' : src_item})

    if ARGS.outputfile == 'stdout':
        print(json.dumps(target_dict, indent=4))
    else:
        with open(ARGS.outputfile, 'w', encoding='utf8') as outputobject:
            outputobject.write(json.dumps(target_dict, indent=4))

### class ###
class SumoApiClient():
    """
    This is defined SumoLogic API Client
    The class includes the HTTP methods, cmdlets, and init methods
    """

    def __init__(self, access_id, access_key, endpoint=None, cookie_file='cookies.txt'):
        """
        Initializes the Sumo Logic object
        """

        self.session = requests.Session()
        self.session.auth = (access_id, access_key)
        self.session.headers = {'content-type': 'application/json', \
            'accept': 'application/json'}
        cookiejar = http.cookiejar.FileCookieJar(cookie_file)
        self.session.cookies = cookiejar
        if endpoint is None:
            self.endpoint = self._get_endpoint()
        elif len(endpoint) < 3:
            self.endpoint = 'https://api.' + endpoint + '.sumologic.com/api'
        else:
            self.endpoint = endpoint
        if self.endpoint[-1:] == "/":
            raise Exception("Endpoint should not end with a slash character")

    def _get_endpoint(self):
        """
        SumoLogic REST API endpoint changes based on the geo location of the client.
        It contacts the default REST endpoint and resolves the 401 to get the right endpoint.
        """
        self.endpoint = 'https://api.sumologic.com/api'
        self.response = self.session.get('https://api.sumologic.com/api/v1/collectors')
        endpoint = self.response.url.replace('/v1/collectors', '')
        return endpoint

    def delete(self, method, params=None, headers=None, data=None):
        """
        Defines a Sumo Logic Delete operation
        """
        response = self.session.delete(self.endpoint + method, \
            params=params, headers=headers, data=data)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def get(self, method, params=None, headers=None):
        """
        Defines a Sumo Logic Get operation
        """
        response = self.session.get(self.endpoint + method, \
            params=params, headers=headers)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def post(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Post operation
        """
        response = self.session.post(self.endpoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def put(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Put operation
        """
        response = self.session.put(self.endpoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

#### class ###
### methods ###

    def get_connections(self, limit=1000, token=''):
        """
        collect information on connections
        """
        params = {'limit': limit, 'token': token}
        url = '/v1/connections/'
        body = self.get(url, params=params).text
        results = json.loads(body)
        return results

    def create_connection(self, jsonpayload):
        """
        create a connection
        """
        if ARGS.jsonfile:
            with open(ARGS.jsonfile, "r", encoding='utf8') as fileobject:
                jsonpayload = ast.literal_eval((fileobject.read()))

        if ARGS.verbose:
            print(jsonpayload)

        if ARGS.overrides:
            for override in ARGS.overrides:
                or_key, or_value = override.split('=')
                jsonpayload[or_key] = or_value

        if ARGS.verbose:
            print(jsonpayload)

        url = "/v1/connections"
        body = self.post(url, json.dumps(jsonpayload)).text
        results = json.loads(body)
        return results

    def get_connection(self, item_id):
        """
        get information on a connection
        """
        url = '/v1/connections/' + str(item_id)
        body = self.get(url).text
        results = json.loads(body)
        return results

    def delete_connection(self, item_id):
        """
        delete a connection
        """
        url = '/v1/connections/' + str(item_id)
        results = self.delete(url).text
        return results

### methods ###

if __name__ == '__main__':
    main()
