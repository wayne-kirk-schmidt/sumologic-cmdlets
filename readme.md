Sumo Logic Cmdlets
==================

Sumo=Logic Cmdlets are small scriptlets to get, create, run, list, query, and delete sumologic objects.
They are designed to be put into Ansible, Chef or other DevOps tools to promote "Sumo Logic Config as code"

Installing the Scripts
=======================

The scripts are command line based, designed to be used within a batch script or DevOPs tool such as Chef or Ansible.
Each script is a python3 script, and the complete list of the python modules will be provided to aid people using a pip install.

You will need to use Python 3.6 or higher and the modules listed in the dependency section.  

The steps are as follows: 

    1. Download and install python 3.6 or higher from python.org. Append python3 to the LIB and PATH env.

    2. Download and install git for your platform if you don't already have it installed.
       It can be downloaded from https://git-scm.com/downloads
    
    3. Open a new shell/command prompt. It must be new since only a new shell will include the new python 
       path that was created in step 1. Cd to the folder where you want to install the scripts.
    
    4. Execute the following command to install pipenv, which will manage all of the library dependencies:
    
        sudo -H pip3 install pipenv 
 
    5. Clone this repository. This will create a new folder
    
    6. Change into this folder. Type the following to install all the package dependencies 
       (this may take a while as this will download all of the libraries it uses):

        pipenv install

Using the Scripts
=================

In general the following are requred to be set either as an env var or an argument.

Argument: MY_APIKEY
You must supply this argument or have preset the env vars
format: <key>:<secret> and will split into: SUMO_UID:SUMO_KEY


```
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
```

Argument: ARGS.MY_CLIENT
format: DEPLOYMENT_ORGID and will split to: SUMO_LOC_SUMO_ORG

This corresponds to the env vars:
```
    os.environ['SUMO_LOC'] = MY_DEPLOYMENT
    os.environ['SUMO_ORG'] = MY_ORGID
    os.environ['SUMO_TAG'] = ARGS.MY_CLIENT
```

Argument: ARGS.MY_ENDPOINT
This is the api endpoint code such as au,us2 etc.
```
    os.environ['SUMO_END'] = ARGS.MY_ENDPOINT
```

Example: running a query
========================

Assuming the env vars are setup SUMO_UID,SUMO_KEY, to run a query job we might do:
```
./bin/run/sumoquery.py -t 'abc_1234' -q '_sourcecategory=* | limit 10| count by _sourcecategory'
```

sumoquery exports **records** rather than messages in a csv format to /var/tmp/sumoquery/outputs/

A dir is created for based on the output job tagging such as -t 'abc_1234' would reult in:
/var/tmp/sumoquery/outputs/sumoquery.abc_1234.001.csv 

Example: List connections in csv format to console
==================================================

With env vars set such as SUMO_ORG=abcd
```
./bin/list/sumocli_list_connections.py 
abcd,connection,test,0000000000022363
```

Example: Export roles in json format
====================================
This exports a json object role object containing an array of roles.

```
bin/query/sumocli_query_roles.py
```

Data set has some tagging added (with intention it could be used on multiple instances)
```
{
    "orgid": "abcd",
    "role": {
        "00000000005854F7": {
            "parent": "abcd",
            "id": "00000000005854F7",
            "name": "Administrator",
            "dump": {
                "name": "Administrator",
                "description": "",
                "filterPredicate": "*",
```
      
Dependencies
============

See the contents of "pipfile"

Script Names and Purposes
=========================

The scripts are organized into sub directories:

    1. ./bin - has all of the scripts to get, create, delete, update, list, and so on.
       Sample is here:
          ./bin/get/sumocli_get_gfolders.py
          ./bin/get/sumocli_get_folders.py
          ./bin/get/sumocli_get_fers.py
          ./bin/get/sumocli_get_collectors.py
          ./bin/get/sumocli_get_partitions.py
          ./bin/get/sumocli_get_sources.py
          ./bin/get/sumocli_get_roles.py
          ./bin/get/sumocli_get_users.py
          ./bin/get/sumocli_get_views.py
          ./bin/get/sumocli_get_monitors.py
          ./bin/get/sumocli_get_connections.py
          ./bin/get/sumocli_get_dynamicrules.py
       Other verbs will be built around these, such as import, export, acrhive, etc.
       There will be a manifest of all of the scripts/verbs in etc as well

    2. ./lib - has samples of templates for both the python script and templates.
    3. ./etc - has an example of a config file to set ENV variables for access

To Do List:
===========

* Build an Ansible wrapper for the scripts

* Add dependency checking for pip modules

License
=======

Copyright 2019 - 2022 Wayne Kirk Schmidt
https://www.linkedin.com/in/waynekirkschmidt

Licensed under the Apache 2.0 License (the "License");

You may not use this file except in compliance with the License.
You may obtain a copy of the License at

    license-name   APACHE 2.0
    license-url    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Support
=======

Feel free to e-mail me with issues to: 

*    wschmidt@sumologic.com

*    wayne.kirk.schmidt@gmail.com

I will provide "best effort" fixes and extend the scripts.
