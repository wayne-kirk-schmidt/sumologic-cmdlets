#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: create_collectors a cmdlet within the sumocli that builds an object

Usage:
   $ python  create_collectors [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_create_collectors
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

create_collectors is part of sumocli, a tool which wraps the Sumologic API.
It meshes with DevOps practices and allows teams to query, audit, backup, 
and manage sumologic deployments in an agile and modular way.

""")

PARSER.add_argument("-u", metavar='<uid>', dest='MY_UID', help="Set Sumo apiuid")
PARSER.add_argument("-k", metavar='<key>', dest='MY_KEY', help="Set Sumo apikey")
PARSER.add_argument("-a", metavar='<api>', dest='MY_API', help="Set Sumo apiservice")
PARSER.add_argument("-o", metavar='<org>', dest='MY_ORG', help="Set Sumo orgid")

PARSER.add_argument("-c", metavar='<cfg>', dest='MY_CFG', help="Set Sumo configfile")

PARSER.add_argument("-f", metavar='<fmt>', default="list", dest='oformat', \
                    help="Specify output format (default = list )")

PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='verbose', help="Increase verbosity")

PARSER.add_argument("-n", "--noexec", action='store_true', \
                    help="Print but do not execute commands")

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
    SUMO_ORG = os.environ['SUMO_ORG']
except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

PP = pprint.PrettyPrinter(indent=4)
SUMO_CRED = SUMO_UID + ':' + SUMO_KEY


def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    src = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_API)
    run_sumo_cmdlet(src)

def run_sumo_cmdlet(src):
    """
    This will create the object. The goal is make the script single object and purpose
    If there are dependencies for the creation, this will handle them.
    """
    target_object = "collector"
    target_dict[target_object] = dict()

    ### def create_collector(self, collectorType, name, description, category):

    target_collector = src.create_collector()
    target_collector_id = target_dict[target_object]['id']
    target_collector_results = src.confirm_collector(target_collector_id)

    print(json.dumps(target_collector_results, indent=4))

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

### included code

    """
    https://help.sumologic.com/APIs/01Collector-Management-API/Collector-API-Methods-and-Examples#POST_methods
    """
    def create_collector(self, collectorType, name, description, category):
        url = self.base_url + "/v1/collectors"
        data = {
            'collector': {
                'collectorType': collectorType,
                'name': name,
                'description': description,
                'category': category,
            }
        }
        return self.__http_post(url, data)

    def confirm_collector(self, myself):
        """
        Using an HTTP client, this uses a GET to confirm the details of the collector creation
        """
        url = self.base_url + "/v1/collectors/" + str(myself)
        return self.__http_get(url)['collector']

### included code

if __name__ == '__main__':
    main()
