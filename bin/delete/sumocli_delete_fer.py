#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=R0913

"""
Exaplanation: detele_fer a sumocli cmdlet creating field extraction rules

Usage:
   $ python  delete_fer [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_delete_fer
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
delete_fer is a Sumo Logic cli cmdlet creating a specific fer
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
    target_object = "source"
    target_dict = {}
    target_dict["orgid"] = SUMO_ORG
    target_dict[target_object] = {}

    src_item = source.get_fer(MYSELFID)
    if str(src_item['id']) == str(MYSELFID):
        target_dict[src_item['id']] = {}
        target_dict[src_item['id']].update({'parent' : SUMO_ORG})
        target_dict[src_item['id']].update({'id' : src_item['id']})
        target_dict[src_item['id']].update({'name' : src_item['name']})
        target_dict[src_item['id']].update({'dump' : src_item})

    with open(BACKUP_TARGET, 'w', encoding='utf8') as outputobject:
        outputobject.write(json.dumps(target_dict, indent=4))

    _results = source.delete_fer(MYSELFID)

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

    def get_fers(self, limit=1000, token=''):
        """
        lists all Field Extraction Rules (FER)
        """
        params = {'limit': limit, 'token': token}
        response = self.get('/v1/extractionRules', params=params)
        return json.loads(response.text)

    def create_fer(self, fer_name, fer_scope, fer_parse_expression, fer_enabled=False):
        """
        create a specific FER
        """
        object_type = 'fer'
        jsonpayload = {
            'name': object_type + '_' + fer_name,
            'scope': object_type + '_' + fer_scope,
            'parseExpression': fer_parse_expression,
            'enabled': fer_enabled
        }
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

        url = "/v1/extractionRules"
        body = self.post(url, jsonpayload).text
        results = json.loads(body)
        return results

    def get_fer(self, item_id):
        """
        get details on a specific FER
        """
        response = self.get('/v1/extractionRules/' + str(item_id))
        return json.loads(response.text)

    def update_fer(self, item_id, fer_name, fer_scope, fer_parse, enabled=False):
        """
        update details on a specific FER
        """
        data = {
                   'name': fer_name,
                   'scope': fer_scope,
                   'parseExpression': fer_parse,
                   'enabled': str(enabled).lower()
               }
        response = self.put('/v1/extractionRules/' + str(item_id), data)
        return json.loads(response.text)

    def delete_fer(self, myselfid):
        """
        delete a specific FER
        """
        url = "/v1/extractionRules/" + str(myselfid)
        results = self.delete(url).text
        return results

### methods ###

if __name__ == '__main__':
    main()
