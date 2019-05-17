#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: sumoget a means to collect information from sumo installations

Usage:
   $ python  sumoget [ options ] <object>

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumoget
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   GNU GPL
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

import urllib.request
import base64
import json
import pprint
import os
import sys
import argparse
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""

sumocli is a command line interface to SumoLogic API
it aallows your security and devops teams to perform
audits, devops, health checks, and other tasks and
enabling you to have all items as code.

""")

PARSER.add_argument("-u", "--uid", metavar='<uid>', dest='MY_UID', help="Set Sumo Uid")
PARSER.add_argument("-k", "--key", metavar='<key>', dest='MY_KEY', help="Set Sumo Key")
PARSER.add_argument("-a", "--api", metavar='<api>', dest='MY_API', help="Set Sumo API")
PARSER.add_argument("-o", "--org", metavar='<org>', dest='MY_ORG', help="Set Sumo Org")
PARSER.add_argument("-c", "--cfg", metavar='<cfg>', dest='MY_CFG', help="Set Sumo Config File")

PARSER.add_argument("-v", type=int, default=0, metavar='<int>', \
                    dest='verbose', help="Increase verbosity")
PARSER.add_argument("-n", action='store_true', help="Print but do not execute commands")

ARGS = PARSER.parse_args()

if ARGS.MY_UID:
    os.environ["SUMO_UID"] = ARGS.MY_UID
if ARGS.MY_KEY:
    os.environ["SUMO_KEY"] = ARGS.MY_KEY
if ARGS.MY_ORG:
    os.environ["SUMO_ORG"] = ARGS.MY_ORG
if ARGS.MY_API:
    os.environ["SUMO_API"] = ARGS.MY_API

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_API = os.environ['SUMO_API']
except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

### SUMO_CRED = SUMO_UID + ':' + SUMO_KEY

PP = pprint.PrettyPrinter(indent=4)
SUMO_CRED = SUMO_UID + ':' + SUMO_KEY


def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    src = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_API)
    list_collectors(src)

def list_collectors(src):
    """
    First enumerate through all collectors and then for each, collect the sources.
    There are two methods;
      + the first is collect the list of sources per collectors
      + and the second is scoop the JSON
    """
    src_cols = src.get_collectors()
    for src_col in src_cols:
        src_sources = src.get_sources(src_col['id'])
        my_cid = src_col['id']
        src_sources = src.get_sources(my_cid)
        for src_source in src_sources:
            if ARGS.verbose > 0:
                print('COLLECTOR :: {} :: {} :: {} ::'.format(src_col['id'], \
                      src_col['name'], src_source['name']))
        src_contents = src.get_source_contents(my_cid, SUMO_CRED)
        src_list = src_contents['sources']
        for src_item in src_list:
            src_n = src_item['name']
            src_e = src_item['encoding']
            src_t = src_item['sourceType']
            src_c = 'undefined'
            if 'category' in src_item:
                src_c = src_item['category']
            src_x = 'undefined'
            if 'script' in src_item:
                src_x = src_item['script']
            if ARGS.verbose > 4:
                print('COLLECTOR :: {} :: SOURCE :: {} :: {} :: {} :: {} :: {} ::'.format(
                    my_cid, src_n, src_e, src_t, src_c, src_x))

class SumoApiClient():
    """
    This is the boilerplate of the SumoAPI client. It will
    create header, get, put, and http methods.

    Once this is done, then it will use the API to issue the appropriate request
    """

    def __init__(self, access_id, access_key, region):
        """
        This sets up the API URL to base requests from.
        Future versions will be able to get a list of all deployments, and find the appropriate one.
        """
        self.access_id = access_id
        self.access_key = access_key
        self.base_url = 'https://api.' + region + '.sumologic.com/api'

    def get_collectors(self):
        """
        Using an HTTP client, this uses a GET to retrieve the collector information.
        """
        url = self.base_url + "/v1/collectors"
        return self.__http_get(url)['collectors']

    def get_sources(self, collector_id):
        """
        Using an HTTP client, this lists the sources for a given collector ID,
        but does not return the JSON
        """
        url = self.base_url + "/v1/collectors/" + str(collector_id) + '/sources'
        return self.__http_get(url)['sources']

    def get_source_contents(self, collector_id, creds):
        """
        Using an HTTP client, this will collect the JSON by appending downlload to stream data.
        """
        url = self.base_url + "/v1/collectors/" + str(collector_id) + '/sources' + '?download=true'
        if ARGS.verbose > 1:
            print('curl -u {} -X GET {}'.format(creds, url))
        return self.__http_get(url)

    def __http_get(self, url):
        """
        Using an HTTP client, this creates a GET for read actions
        """
        if ARGS.verbose > 8:
            print('http get from: ' + url)
        req = urllib.request.Request(url, headers=self.__create_header())
        with urllib.request.urlopen(req) as res:
            body = res.read()
            return json.loads(body)

    def __http_post(self, url, data):
        """
        Using an HTTP client, this creates a POST for write actions
        """
        json_str = json.dumps(data)
        post = json_str.encode('utf-8')
        if ARGS.verbose > 8:
            print('http post to: ' + url)
            print('http post data: ' + json_str)
        req = urllib.request.Request(url, data=post, method='POST', headers=self.__create_header())
        with urllib.request.urlopen(req) as res:
            body = res.read()
            return json.loads(body)

    def __create_header(self):
        """
        Using an HTTP client, this constructs the header, providing the access credentials
        """
        basic = base64.b64encode('{}:{}'.format(self.access_id, self.access_key).encode('utf-8'))
        return {"Authorization": "Basic " + basic.decode('utf-8'), \
        "Content-Type": "application/json"}

if __name__ == '__main__':
    main()
