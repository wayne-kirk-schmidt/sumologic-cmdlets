#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: run_query is a Sumo Logic cmdlet that manages a query

Usage:
   $ python  run_query [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_run_query
    @version        0.80
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   GNU GPL
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 0.80
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

import json
import pprint
import os
import sys
import time
import argparse
import http
import re
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""

run_query is a cmdlet managing queries.

""")

PARSER.add_argument("-c", metavar='<cfg>', dest='MY_CFG', \
                    help="set Sumo run config")
PARSER.add_argument("-a", metavar='<api>', dest='MY_API', \
                    help="set Sumo api ( format: <key>:<secret> ) ")
PARSER.add_argument("-k", metavar='<key>', dest='MY_KEY', \
                    help="set Sumo key ( format: <site>:<orgid> ) ")
PARSER.add_argument("-j", metavar='<job>', dest='MY_JOB', \
                    help="set Sumo job config")
PARSER.add_argument("-q", metavar='<query>', dest='MY_QUERY', \
                    help="set Sumo job query")
PARSER.add_argument("-r", metavar='<range>', dest='MY_RANGE', default='1h', \
                    help="set Sumo job range")
PARSER.add_argument("-o", metavar='<fmt>', default="list", dest='oformat', \
                    help="set output format ( format: json, csv )")
PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='VERBOSE', help="Increase verbosity")

ARGS = PARSER.parse_args()

SEC_M = 1000
MIN_S = 60
HOUR_M = 60
DAY_H = 24
WEEK_D = 7

LIMIT = 10000

DEFAULT_QUERY = '''
_index=sumologic_volume
| count by _sourceCategory
'''

QUERY_EXT = '.qry'

NOW_TIME = int(time.time()) * SEC_M

TIME_TABLE = dict()
TIME_TABLE["s"] = SEC_M
TIME_TABLE["m"] = TIME_TABLE["s"] * MIN_S
TIME_TABLE["h"] = TIME_TABLE["m"] * HOUR_M
TIME_TABLE["d"] = TIME_TABLE["h"] * DAY_H
TIME_TABLE["w"] = TIME_TABLE["d"] * WEEK_D

TIME_PARAMS = dict()

if ARGS.MY_API:
    os.environ["SUMO_API"] = ARGS.MY_API
    (MY_APINAME, MY_APISECRET) = os.environ["MY_API"].split(':')
    os.environ["SUMO_UID"] = MY_APINAME
    os.environ["SUMO_KEY"] = MY_APISECRET

if ARGS.MY_KEY:
    os.environ["SUMO_KEY"] = ARGS.MY_KEY
    (MY_DEPLOYMENT, MY_ORGID) = os.environ["MY_KEY"].split('_')
    os.environ["SUMO_LOC"] = MY_DEPLOYMENT
    os.environ["SUMO_ORG"] = MY_ORGID

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_LOC = os.environ['SUMO_LOC']
    SUMO_ORG = os.environ['SUMO_ORG']

except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

PPRINT = pprint.PrettyPrinter(indent=4)

def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """

    src = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_LOC)

    time_params = calculate_range()

    query_list = collect_queries()
    for query_item in query_list:
        run_sumo_cmdlet(src, collect_contents(query_item), time_params)

def calculate_range():
    """
    This calculates time ranges based on range from current day
    If specified "NNX to MMY" then NNX is start and MMY is finish
    """

    number = 1
    period = "h"

    if ARGS.MY_RANGE:
        number = re.match(r'\d+', ARGS.MY_RANGE.replace('-', ''))
        period = ARGS.MY_RANGE.replace(number.group(), '')

    time_to = NOW_TIME
    time_from = time_to - (int(number.group()) * int(TIME_TABLE[period]))
    TIME_PARAMS["time_to"] = time_to
    TIME_PARAMS["time_from"] = time_from
    TIME_PARAMS["time_zone"] = 'UTC'
    TIME_PARAMS["by_receipt_time"] = False
    return TIME_PARAMS

def collect_queries():
    """
    Scoop up a query if a directory, file or a string
    If a directory then it will process based on .qry extension
    """

    query_list = []

    if ARGS.MY_QUERY:
        if os.path.isfile(ARGS.MY_QUERY):
            query_list.append(ARGS.MY_QUERY)
        elif os.path.isdir(ARGS.MY_QUERY):
            for root, _dirs, files in os.walk(ARGS.MY_QUERY):
                for file in files:
                    if os.path.splitext(file)[1] == QUERY_EXT:
                        fullpath = os.path.join(root, file)
                        query_list.append(fullpath)
    else:
        query_list.append(DEFAULT_QUERY)
    return query_list

def collect_contents(query_item):
    """
    Scoop up a query if a directory, file or a string
    If a directory then it will process based on .sqy extension
    """
    query = query_item
    if os.path.exists(query_item):
        file_object = open(query_item, "r")
        query = file_object.read()
        file_object.close()
    return query

def run_sumo_cmdlet(src, query, time_params):
    """
    This runs the Sumo Command, and then saves the ooutput and the status
    """

    query_job = src.search_job(query, time_params)
    query_jobid = query_job["id"]

    (query_status, num_records, iterations) = src.search_job_records_tally(query_jobid)
    if ARGS.VERBOSE:
        print('::{}::{}::{}::{}::'.format(query_jobid, query_status, num_records, iterations))

    query_records = src.search_job_records(query_jobid, LIMIT, 0)
    if ARGS.VERBOSE:
        print(query_records)

    query_messages = src.search_job_messages(query_jobid, LIMIT, 0)
    if ARGS.VERBOSE:
        print(query_messages)

    fields = query_records["fields"]
    for field in fields:
        fieldname = field["name"]
        sys.stdout.write('{:40s}\t'.format(str(fieldname)))
    print("")

    for record in query_records["records"]:
        linestring = ''
        for field in fields:
            fieldname = field["name"]
            ### value = str(record["map"][fieldname])
            linestring += str(record["map"][fieldname]) + ','
            sys.stdout.write('{:40s}\t'.format(str(record["map"][fieldname])))
        print("")
        ### print(s[0:-1] + '\n')

    ### query_messages = src.search_job_messages(query_job, LIMIT, 0)
    ### print(query_messages)

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

### included code

    def search_job(self, query, time_params):

        """
        Run a search job
        """

        time_from = time_params["time_from"]
        time_to = time_params["time_to"]
        time_zone = time_params["time_zone"]
        by_receipt_time = time_params["by_receipt_time"]

        data = {
            'query': str(query),
            'from': str(time_from),
            'to': str(time_to),
            'timeZone': str(time_zone),
            'byReceiptTime': str(by_receipt_time)
        }
        response = self.post('/v1/search/jobs', data)
        return json.loads(response.text)

    def search_job_status(self, search_jobid):
        """
        Find out search job status
        """
        response = self.get('/v1/search/jobs/' + str(search_jobid))
        return json.loads(response.text)

    def search_job_records_tally(self, query_jobid):
        """
        Find out search job records
        """
        query_output = self.search_job_status(query_jobid)
        query_status = query_output['state']
        num_records = query_output['recordCount']
        time.sleep(1)
        iterations = 1
        while query_status == 'GATHERING RESULTS':
            query_output = self.search_job_status(query_jobid)
            query_status = query_output['state']
            num_records = query_output['recordCount']
            time.sleep(1)
            iterations += 1
        return (query_status, num_records, iterations)

    def calculate_and_fetch_records(self, query_jobid, num_records):
        """
        Calculate and return records in chunks based on LIMIT
        """
        job_records = []
        iterations = num_records // LIMIT + 1
        for iteration in range(1, iterations + 1):
            records = self.search_job_records(query_jobid, limit=LIMIT,
                                              offset=((iteration - 1) * LIMIT))
            for record in records['records']:
                job_records.append(record)

        return job_records

    def search_job_messages_tally(self, query_jobid):
        """
        Find out search job messages
        """
        query_output = self.search_job_status(query_jobid)
        query_status = query_output['state']
        num_messages = query_output['messageCount']
        time.sleep(1)
        iterations = 1
        while query_status == 'GATHERING RESULTS':
            query_output = self.search_job_status(query_jobid)
            query_status = query_output['state']
            num_messages = query_output['messageCount']
            time.sleep(1)
            iterations += 1
        return (query_status, num_messages, iterations)

    def calculate_and_fetch_messages(self, query_jobid, num_messages):
        """
        Calculate and return messages in chunks based on LIMIT
        """
        job_messages = []
        iterations = num_messages // LIMIT + 1
        for iteration in range(1, iterations + 1):
            records = self.search_job_records(query_jobid, limit=LIMIT,
                                              offset=((iteration - 1) * LIMIT))
            for record in records['records']:
                job_messages.append(record)
        return job_messages

    def search_job_messages(self, query_jobid, limit=None, offset=0):
        """
        Query the job messages of a search job
        """
        params = {'limit': limit, 'offset': offset}
        response = self.get('/v1/search/jobs/' + str(query_jobid) + '/messages', params)
        return json.loads(response.text)

    def search_job_records(self, query_jobid, limit=None, offset=0):
        """
        Query the job records of a search job
        """
        params = {'limit': limit, 'offset': offset}
        response = self.get('/v1/search/jobs/' + str(query_jobid) + '/records', params)
        return json.loads(response.text)

    def delete_search_job(self, query_jobid):
        """
        Delete an unused search job
        """
        return self.delete('/v1/search/jobs/' + str(query_jobid))

### included code


if __name__ == '__main__':
    main()
