#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: sumo_logic_template is a Sumo Logic cmdlet

Usage:
   $ python  sumo_logic_template [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumo_logic_template
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   GNU GPL
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

### beginning ###
import json
import pprint
import os
import sys
import argparse
import http
import re
import time
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
sumo_logic_template is a Sumo Logic cli cmdlet
""")

PARSER.add_argument("-a", metavar='<secret>', dest='MY_SECRET', \
                    help="set api (format: <key>:<secret>) ")
PARSER.add_argument("-k", metavar='<client>', dest='MY_CLIENT', \
                    help="set key (format: <site>_<orgid>) ")
PARSER.add_argument("-e", metavar='<endpoint>', default='us2', dest='MY_ENDPOINT', \
                    help="set endpoint (format: <endpoint>) ")
PARSER.add_argument("-q", metavar='<query>', dest='MY_QUERY', help="set query_content")
PARSER.add_argument("-r", metavar='<range>', dest='MY_RANGE', default='1h', \
                    help="set query_range")
PARSER.add_argument("-o", metavar='<fmt>', default="csv", dest='OUT_FORMAT', \
                    help="set query_output (values: txt, csv)")
PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='VERBOSE', help="increase verbosity")

ARGS = PARSER.parse_args()

SEC_M = 1000
MIN_S = 60
HOUR_M = 60
DAY_H = 24
WEEK_D = 7

LIMIT = 10000
LONGQUERY_LIMIT = 100

DEFAULT_QUERY = '''
_index=sumologic_volume
| count by _sourceCategory
'''

QUERY_EXT = '.sqy'

CSV_SEP = ','
TAB_SEP = '\t'
EOL_SEP = '\n'

MY_SEP = CSV_SEP
if ARGS.OUT_FORMAT == 'txt':
    MS_SEP = TAB_SEP

NOW_TIME = int(time.time()) * SEC_M

TIME_TABLE = dict()
TIME_TABLE["s"] = SEC_M
TIME_TABLE["m"] = TIME_TABLE["s"] * MIN_S
TIME_TABLE["h"] = TIME_TABLE["m"] * HOUR_M
TIME_TABLE["d"] = TIME_TABLE["h"] * DAY_H
TIME_TABLE["w"] = TIME_TABLE["d"] * WEEK_D

TIME_PARAMS = dict()

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
    SUMO_END = os.environ['SUMO_END']
except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

PPRINT = pprint.PrettyPrinter(indent=4)

### beginning ###

def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """

    source = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)

### class ###
class SumoApiClient():
    """
    This is defined SumoLogic API Client
    The class includes the HTTP methods, cmdlets, and init methods
    """

    def __init__(self, access_id, access_key, region, cookieFile='cookies.txt'):
        """
        Initializes the Sumo Logic object
        """
        self.session = requests.Session()
        self.session.auth = (access_id, access_key)
        self.session.headers = {'content-type': 'application/json', \
            'accept': 'application/json'}
        self.endpoint = 'https://api.' + region + '.sumologic.com/api'
        cookiejar = http.cookiejar.FileCookieJar(cookieFile)
        self.session.cookies = cookiejar

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

### class ###
### methods ###

### methods ###

if __name__ == '__main__':
    main()
