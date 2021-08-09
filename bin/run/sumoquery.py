#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: sumoquery is a Sumo Logic cmdlet that manages a query

Usage:
   $ python  sumoquery [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumoquery
    @version        1.10
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   GNU GPL
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
import re
import time
import random
import multiprocessing
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas
import boto3

sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
run_query is a Sumo Logic cli cmdlet managing queries
""")

PARSER.add_argument("-a", metavar='<secret>', dest='MY_APIKEY', \
                    help="set query authkey (format: <key>:<secret>) ")
PARSER.add_argument("-e", metavar='<endpoint>', dest='MY_ENDPOINT', \
                    help="set query endpoint (format: <dep>) ")
PARSER.add_argument("-t", metavar='<targetorg>', dest='MY_TARGET', \
                    action='append', help="set query target  (format: <dep>_<orgid>) ")
PARSER.add_argument("-q", metavar='<query>', dest='MY_QUERY', help="set query content")
PARSER.add_argument("-r", metavar='<range>', dest='MY_RANGE', default='1h', \
                    help="set query range")
PARSER.add_argument("-o", metavar='<fmt>', default="csv", dest='OUT_FORMAT', \
                    help="set query output (values: txt, csv)")
PARSER.add_argument("-d", metavar='<outdir>', default="/var/tmp", dest='OUTPUTDIR', \
                    help="set query output directory")
PARSER.add_argument("-s", metavar='<sleeptime>', default=2, dest='SLEEPTIME', \
                    help="set sleep time to check results")
PARSER.add_argument("-w", metavar='<workers>', type=int, default=1, dest='WORKERS', \
                    help="set number of workers to process")
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

MY_SLEEP = int(ARGS.SLEEPTIME)

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

TARGETS = ARGS.MY_TARGET

if ARGS.MY_APIKEY:
    (MY_APINAME, MY_APISECRET) = ARGS.MY_APIKEY.split(':')
    os.environ['SUMO_UID'] = MY_APINAME
    os.environ['SUMO_KEY'] = MY_APISECRET

if "aws:ssm:" in ARGS.MY_APIKEY:
    VENDOR, METHOD, REGION, TOKENS = ARGS.MY_APIKEY.split(':')
    if ARGS.VERBOSE > 7:
        print('VENDOR: {}'.format(VENDOR))
        print('METHOD: {}'.format(METHOD))
        print('REGION: {}'.format(REGION))
        print('TOKENS: {}'.format(TOKENS))

    ssmobject = boto3.client(METHOD, region_name=REGION)
    ssmresponse = ssmobject.get_parameters(
        Names=[ TOKENS ],
        WithDecryption=True
    )

    TOKEN_CONTENTS = ssmresponse['Parameters'][0]['Value']
    (MY_APINAME, MY_APISECRET) = TOKEN_CONTENTS.split(':')
    os.environ['SUMO_UID'] = MY_APINAME
    os.environ['SUMO_KEY'] = MY_APISECRET

if ARGS.MY_ENDPOINT:
    os.environ['SUMO_END'] = ARGS.MY_ENDPOINT

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_END = os.environ['SUMO_END']

except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

### beginning ###

def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """

    apisession = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)
    query_targets = resolve_targets(TARGETS)
    query_list = collect_queries()
    time_params = calculate_range()

    if ARGS.WORKERS == 1:
        process_request(apisession, query_targets, query_list, time_params)
    else:
        worker_manager(query_targets)

def worker_task(inputs):
    """
    This is the worker task function
    """
    apisession = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)
    query_list = collect_queries()
    time_params = calculate_range()
    workerpid = multiprocessing.current_process()
    if ARGS.VERBOSE > 5:
        print('SUMOQUERY.worker: {}'.format(workerpid))
        print('SUMOQUERY.worktarget: {}'.format(inputs))

    query_targets = list()
    query_targets.append(inputs)

    process_request(apisession, query_targets, query_list, time_params)

def worker_manager(query_targets):
    """
    This is the manager function to handle mapping tasks to workers
    """
    worker_list = query_targets
    with multiprocessing.Pool(ARGS.WORKERS) as task_queue:
        task_queue.map(worker_task, worker_list)

def process_request(apisession, query_targets, query_list, time_params):
    """
    perform the queries and process the output
    """
    for query_target in query_targets:
        querycounter = 1
        for query_item in query_list:
            query_data = collect_contents(query_item)
            query_data = tailor_queries(query_data, query_target)
            if ARGS.VERBOSE > 7:
                print('SUMOQUERY.query_item: {}'.format(query_item))
                print('SUMOQUERY.query_data: {}'.format(query_data))
            header_output = run_sumo_query(apisession, query_data, time_params)
            write_query_output(header_output, query_target, querycounter)
            querycounter += 1
            time.sleep(random.randint(0,MY_SLEEP))
        time.sleep(random.randint(0,MY_SLEEP))

def resolve_targets(target_org_list):
    """
    Resolve targets based on input
    """
    query_targets = list()

    for target_org in target_org_list:
        if os.path.isfile(target_org):
            with open(target_org) as input_file:
                input_lines = [input_line.rstrip() for input_line in input_file]
                query_targets += input_lines
        else:
            query_targets.append(target_org)

    return query_targets

def write_query_output(header_output, query_target, query_number):
    """
    This is a wrapper for writing out the contents of a file
    """

    ext_sep = '.'

    querytag = SUMO_END + '.' + query_target

    extension = ARGS.OUT_FORMAT
    number = '{:03d}'.format(query_number)

    output_dir = os.path.abspath(ARGS.OUTPUTDIR)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = ext_sep.join((querytag, str(number), extension))
    output_target = os.path.join(output_dir, output_file)

    if ARGS.VERBOSE > 3:
        print('SUMOQUERY.outputfile: {}'.format(output_target))

    with open(output_target, "w") as file_object:
        file_object.write(header_output + '\n' )
        file_object.close()

def tailor_queries(query_item, query_target):
    """
    This substitutes common parameters for values from the script.
    Later, this will be a data driven exercise.
    """
    replacements = dict()
    replacements['{{deployment}}'] = query_target.split('_')[0]
    replacements['{{org_id}}'] = query_target.split('_')[1]
    replacements['{{longquery_limit_stmt}}'] = str(LONGQUERY_LIMIT)
    replacements['{{key}}'] = query_target
    for sub_key, sub_value in replacements.items():
        query_item = query_item.replace(sub_key, sub_value)
    return query_item

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
        with open(query_item, "r") as file_object:
            query = file_object.read()
            file_object.close()
    return query

def run_sumo_query(apisession, query, time_params):
    """
    This runs the Sumo Command, and then saves the output and the status
    """
    query_job = apisession.search_job(query, time_params)
    query_jobid = query_job["id"]
    if ARGS.VERBOSE > 3:
        print('SUMOQUERY.jobid: {}'.format(query_jobid))

    (query_status, num_messages, num_records, iterations) = apisession.search_job_tally(query_jobid)
    if ARGS.VERBOSE > 4:
        print('SUMOQUERY.status: {}'.format(query_status))
        print('SUMOQUERY.records: {}'.format(num_records))
        print('SUMOQUERY.messages: {}'.format(num_messages))
        print('SUMOQUERY.iterations: {}'.format(iterations))

    assembled_output = build_assembled_output(apisession, query_jobid, num_records, iterations)

    return assembled_output

def build_assembled_output(apisession, query_jobid, num_records, iterations):
    """
    This assembles the header and output, going through the iterations of the output
    """

    if num_records == 0:
        assembled_output = 'NORECORDS'
    if num_records > 0:
        total_records = ''
        for my_counter in range(0, iterations, 1):
            my_limit = LIMIT
            my_offset = ( my_limit * my_counter )

            query_records = apisession.search_job_records(query_jobid, my_limit, my_offset)

            header,header_list = build_header(query_records)
            output = build_body(query_records,header_list)
            total_records = total_records + output

        assembled_output = EOL_SEP.join([ header , total_records ])

    return assembled_output

def build_header(query_records):
    """
    This builds the header of the output from the results of query_records
    """

    header_list = list()
    dataframe = pandas.DataFrame.from_records(query_records['fields'])
    myfielddf = pandas.DataFrame(dataframe, columns=['name'])
    header_list = myfielddf.to_csv(header=None, index=False).strip('\n').split('\n')
    header = MY_SEP.join(header_list)

    return header, header_list

def build_body(query_records, header_list):
    """
    This builds the body of the output from the results of query_records
    """
    record_body_list = list()
    for record in query_records["records"]:
        record_line_list = list()
        for header in header_list:
            recordlist = str(record["map"][header]).replace(',','|')
            record_line_list.append(recordlist)
            record_line = MY_SEP.join(record_line_list)
        record_body_list.append(record_line)
    output = EOL_SEP.join(record_body_list)

    return output

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

        self.retry_strategy = Retry(
            total=6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)

        self.session = requests.Session()

        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)

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

    def search_job_tally(self, query_jobid):
        """
        Find out search job messages
        """
        query_output = self.search_job_status(query_jobid)
        query_status = query_output['state']
        num_messages = query_output['messageCount']
        num_records = query_output['recordCount']
        time.sleep(random.randint(0,MY_SLEEP))
        iterations = 1
        while query_status == 'GATHERING RESULTS':
            query_output = self.search_job_status(query_jobid)
            query_status = query_output['state']
            num_messages = query_output['messageCount']
            num_records = query_output['recordCount']
            time.sleep(random.randint(0,MY_SLEEP))
            iterations += 1
        return (query_status, num_messages, num_records, iterations)

    def calculate_and_fetch_messages(self, query_jobid, num_messages):
        """
        Calculate and return messages in chunks based on LIMIT
        """
        job_messages = []
        iterations = num_messages // LIMIT + 1
        for iteration in range(1, iterations + 1):
            time.sleep(random.randint(0,MY_SLEEP))
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

### methods ###

if __name__ == '__main__':
    main()
