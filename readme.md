SumoLogic Cmdlets
=================

SumoLogic Cmdlets are small scriptlets to get, create, run, list, query, and delete sumologic objects.
They are designed to be put into Ansible, Chef or other DevOps tools to promote "Sumologic Config as code"

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
 
    5. Clone this repo using the following command:
    
        git clone git@github.com:wks-sumo-logic/sumologic-cmdlets.git

    This will create a new folder sumologic-toshokan
    
    6. Change into the sumologic-cmdlets folder. Type the following to install all the package dependencies 
       (this may take a while as this will download all of the libraries that sumotoolbox uses):

        pipenv install
        
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

* Add depdndency checking for pip modules

License
=======

Copyright 2019 Wayne Kirk Schmidt

Licensed under the GNU GPL License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    license-name   GNU GPL
    license-url    http://www.gnu.org/licenses/gpl.html

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Support
=======

Feel free to e-mail me with issues to: wschmidt@sumologic.com
I will provide "best effort" fixes and extend the scripts.

