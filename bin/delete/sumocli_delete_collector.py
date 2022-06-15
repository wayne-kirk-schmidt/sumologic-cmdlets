#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: delete_collector a sumocli cmdlet that removes a collector

Usage:
   $ python  delete_collector [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_delete_collector
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   Apache 2.0
    @license-url    http://www.gnu.org/licenses/gpl.html
"""


__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

### beginning ###
import json
import os
import sys
import argparse
import http
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
delete_collector is a Sumo Logic cli cmdlet deleting a specific collector
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

if ARGS.myselfid:
    os.environ['MYSELFID'] = ARGS.myselfid

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_LOC = os.environ['SUMO_LOC']
    SUMO_ORG = os.environ['SUMO_ORG']
    MYSELFID = os.environ['MYSELFID']
except KeyError as myerror:
    print(f'Environment Variable Not Set :: {myerror.args[0]}')

BACKUP_DIR = '/var/tmp'
BACKUP_FILE = SUMO_LOC + '_' + SUMO_ORG + '.' + MYSELFID + '.' + 'json'
BACKUP_TARGET = os.path.join(BACKUP_DIR, BACKUP_FILE)

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
    target_object = "collector"
    target_dict = {}
    target_dict["orgid"] = SUMO_ORG
    target_dict[target_object] = {}

    src_items = source.get_collectors()
    for src_item in src_items:
        if str(src_item['id']) == str(MYSELFID):
            target_dict[target_object][src_item['id']] = {}
            target_dict[target_object][src_item['id']].update({'parent' : SUMO_ORG})
            target_dict[target_object][src_item['id']].update({'id' : src_item['id']})
            target_dict[target_object][src_item['id']].update({'name' : src_item['name']})
            target_dict[target_object][src_item['id']].update({'dump' : src_item})

    with open(BACKUP_TARGET, 'w', encoding='utf8') as outputobject:
        outputobject.write(json.dumps(target_dict, indent=4))

    src_items = source.delete_collector(MYSELFID)

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

    def get_collectors(self):
        """
        Using an HTTP client, this uses a GET to retrieve all collector information.
        """
        url = "/v1/collectors"
        body = self.get(url).text
        results = json.loads(body)['collectors']
        return results

    def get_collector(self, myselfid):
        """
        Using an HTTP client, this uses a GET to retrieve single collector information.
        """
        url = "/v1/collectors/" + str(myselfid)
        body = self.get(url).text
        results = json.loads(body)['collector']
        return results

    def delete_collector(self, myselfid):
        """
        Using an HTTP client, this uses a DELETE to remove a specific collector
        """
        url = '/v1/collectors/' + str(myselfid)
        results = self.delete(url).text
        return results

### methods ###

if __name__ == '__main__':
    main()
