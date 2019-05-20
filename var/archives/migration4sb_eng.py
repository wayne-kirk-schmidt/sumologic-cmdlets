
# Please run on Python3 (tested on 3.6)
# pip install urllib
import urllib.request
import base64
import json

# Acceess ID and Access Key published at a migration source
src_access_id = 'Please input Access ID created at US region'
src_access_key = 'Please input Access Key created at US region'

# Acceess ID and Access Key published at a migration destination
dest_access_id = 'Please input Access ID created at JP region'
dest_access_key = 'Please input Access Key created at US region'

# The method run once Python program is launched
def main():
        # Creting Sumo Logic API access client
        src = SumoApiClient(src_access_id, src_access_key, 'us2')
        dest = SumoApiClient(dest_access_id, dest_access_key, 'jp')

        # Migration processes
        migrate_collectors(src, dest)  # Migrating Hosted Collector
        migrate_fers(src, dest)        # Migrating Field Extraction Rule
        migrate_views(src, dest)       # Migrating Scheduled Views
        migrate_connections(src, dest) # Migrating Connections
        #migrate_monitors(src, dest)    # Migrating Metric Monitors
        migrate_roles(src, dest)       # Migrating Roles
        migrate_users(src, dest)       # Migrating Users

# Migrate Collector
def migrate_collectors(src, dest):
        print('### Migrating: Hosted Collectors')
        src_collectors = src.get_collectors()
        if len(src_collectors) == 0: return
        dest_collectors = dest.get_collectors()
        dest_collectors_names = [d['name'] for d in dest_collectors]
        for src_collector in src_collectors:
                # Installed Collector is excluded from migration
                if src_collector['collectorType'] != 'Hosted': continue
                # If Hosted Collector is not registered in the migration destination, register newly
                if src_collector['name'] in dest_collectors_names:
                        collector_id = search(dest_collectors, 'name', src_collector['name'])['id']
                else:                            
                        print("Creating Hosted Collector: " + src_collector['name'])
                        collector_id = dest.create_collector(
                                src_collector['collectorType'],
                                src_collector['name'],
                                src_collector['description'] if 'description' in src_collector else '',
                                src_collector['category'] if 'category' in src_collector else '',
                        )['collector']['id']
                # Migrating Source
                src_sources = src.get_sources(src_collector['id'])
                if len(src_sources) == 0: continue
                dest_sources = dest.get_sources(collector_id)
                dest_sources_names = [d['name'] for d in dest_sources]
                for src_source in src_sources:
                        if src_source['name'] in dest_sources_names: continue # 既に登録されている場合は処理しない
                        print("Creating Source: " + src_source['name'] + " to " + src_collector['name'])
                        dest.create_source(collector_id, src_source)

# Migrate Field Extraction Rule
def migrate_fers(src, dest):
        print('### Migrating: Field Extraction Rule')
        src_fers = src.get_fers()
        if len(src_fers) == 0: return
        dest_fers = dest.get_fers()
        dest_fers_names = [d['name'] for d in dest_fers]
        for src_fer in src_fers:
                if src_fer['name'] in dest_fers_names: continue # Do not process if already registered
                print("Creating Field Extraction Rule: " + src_fer['name'])
                dest.create_fer(
                        src_fer['name'], 
                        src_fer['scope'], 
                        src_fer['parseExpression'], 
                        src_fer['enabled']
                )

# Migrate Scheduled Views
def migrate_views(src, dest):
        print('### Migrating: Scheduled Views')
        src_views = src.get_views()
        if len(src_views) == 0: return
        dest_views = dest.get_views()
        dest_views_names = [d['indexName'] for d in dest_views]
        for src_view in src_views:
                if src_view['indexName'] in dest_views_names: continue # Do not process if already registered
                print("Creating Scheduled Views: " + src_view['indexName'])
                dest.create_view(
                        src_view['query'], 
                        src_view['indexName'], 
                        src_view['startTime'], 
                        src_view['retentionPeriod']
                )

# Migrate Connections
def migrate_connections(src, dest):
        print('### Migrating: Connections')
        src_connections = src.get_connections()
        if len(src_connections) == 0: return
        dest_connections = dest.get_connections()
        dest_connections_names = [d['name'] for d in dest_connections]
        for src_connection in src_connections:
                if src_connection['name'] in dest_connections_names: continue # Do not process if already registered
                print("Creating Connection: " + src_connection['name'])
                dest.create_connection(
                        src_connection['type'], 
                        src_connection['name'], 
                        src_connection['description'], 
                        src_connection['url'], 
                        src_connection['headers'], 
                        src_connection['customHeaders'], 
                        src_connection['defaultPayload'], 
                        src_connection['webhookType'])

# Migrate Metric Monitors
def migrate_monitors(src, dest):
        print('### Migrating: Metric Monitors')
        src_monitors = src.get_monitors()
        print(src_monitors)
        if len(src_monitors) == 0: return
        dest_monitors = dest.get_monitors()
        dest_monitors_names = [d['name'] for d in dest_monitors]
        for src_monitor in src_monitors:
                if src_monitor['name'] in dest_monitors_names: continue # Do not process if already registered
                print("Creating Metric Monitor: " + src_monitor['name'])
                dest.create_monitor(
                        src_monitor['name'], 
                        src_monitor['description'], 
                        src_monitor['isDisabled'], 
                        src_monitor['alertQueries'], 
                        src_monitor['queriesTimeRange'], 
                        src_monitor['timeZone'], 
                        src_monitor['monitorRules'], 
                        src_monitor['muteStatus'], 
                        src_monitor['chartSettings']
                )

# Migrate Roles
def migrate_roles(src, dest):
        print('### Migrating: Roles')
        src_roles = src.get_roles()
        dest_roles = dest.get_roles()
        dest_roles_names = [d['name'] for d in dest_roles]
        for src_role in src_roles:
                if src_role['name'] in dest_roles_names: continue # Do not process if already registered
                print("Creating Role: " + src_role['name'])
                dest.create_role(
                        src_role['name'], 
                        src_role['description'], 
                        src_role['filterPredicate'], 
                        [], # Since before user migration, link user ID at creating a new user
                        src_role['capabilities']
                )

# Migrate Users
def migrate_users(src, dest):
        print('### Migrating: Users')
        src_users = src.get_users()
        dest_users = dest.get_users()
        dest_users_email = [d['email'] for d in dest_users]
        dest_rolls = dest.get_roles()
        for src_user in src_users:
                if src_user['email'] in dest_users_email: continue # Do not process if already registered
                print("Creating User: " + src_user['email'])
                dest_rollIds = []
                # List the role ID to which the user belongs
                for src_rollId in src_user['roleIds']:
                        src_roll = src.get_role(src_rollId)
                        dest_roll = search(dest_rolls, 'name', src_roll['name'])
                        dest_rollIds.append(dest_roll['id'])
                dest.create_user(
                        src_user['firstName'], 
                        src_user['lastName'], 
                        src_user['email'], 
                        dest_rollIds
                )

#  Return elements matching the condition from dict in array
def search(arraywithdisc, key, value):
        for d in arraywithdisc:
                if d[key] == value: return d

# Sumo Logic API access client class
# https://api.jp.sumologic.com/docs/
class SumoApiClient():

        # Initialize the instance
        def __init__(self, access_id, access_key, region):
                self.access_id = access_id
                self.access_key = access_key
                self.base_url = 'https://api.' + region + '.sumologic.com/api'

        # Get all Collectors
        # https://help.sumologic.com/APIs/01Collector-Management-API/Collector-API-Methods-and-Examples
        def get_collectors(self):
                url = self.base_url + "/v1/collectors"
                return self.__http_get(url)['collectors']

        # Create new Collector
        # https://help.sumologic.com/APIs/01Collector-Management-API/Collector-API-Methods-and-Examples#POST_methods
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

        # Get all Sources in the Collector
        # https://help.sumologic.com/APIs/01Collector-Management-API/Source-API
        def get_sources(self, collector_id):        
                url = self.base_url + "/v1/collectors/" + str(collector_id) + '/sources'
                return self.__http_get(url)['sources']

        # Add new Source to the Collector
        # https://help.sumologic.com/APIs/01Collector-Management-API/Source-API#POST_methods
        def create_source(self, collector_id, source): 
                url = self.base_url + "/v1/collectors/" + str(collector_id) + '/sources'
                del source['id']
                data = {
                        'source': source
                }
                return self.__http_post(url, data)

        # Get all Field Extraction Rules
        # https://api.jp.sumologic.com/docs/#operation/listExtractionRules
        def get_fers(self):
                url = self.base_url + "/v1/extractionRules"
                return self.__http_get(url)['data']

        # Create new Field Extraction Rule
        # https://api.jp.sumologic.com/docs/#operation/createExtractionRule
        def create_fer(self, name, scope, parseExpression, enabled):
                url = self.base_url + "/v1/extractionRules"
                data = {
                        'name': name,
                        'scope': scope,
                        'parseExpression': parseExpression,
                        'enabled': enabled
                }
                return self.__http_post(url, data)

        # Get all Scheduled Views
        # https://api.jp.sumologic.com/docs/#operation/listScheduledViews
        def get_views(self):
                url = self.base_url + "/v1/scheduledViews"
                return self.__http_get(url)['data']

        # Create new Scheduled View
        # https://api.jp.sumologic.com/docs/#operation/createScheduledView
        def create_view(self, query, indexName, startTime, retentionPeriod):
                url = self.base_url + "/v1/scheduledViews"
                data = {
                        'query': query,
                        'indexName': indexName,
                        'startTime': startTime,
                        'retentionPeriod': retentionPeriod,
                }
                return self.__http_post(url, data)

        # Get all Connections
        # https://api.jp.sumologic.com/docs/#operation/listConnections
        def get_connections(self):
                url = self.base_url + "/v1/connections"
                return self.__http_get(url)['data']

        # Create new Connection
        # https://api.jp.sumologic.com/docs/#operation/createConnection
        def create_connection(self, type, name, description, url, headers, customHeaders, defaultPayload, webhookType):
                url = self.base_url + "/v1/connections"
                if type == 'WebhookConnection': type = 'WebhookDefinition'
                data = {
                        'type': type,
                        'name': name,
                        'description': description,
                        'url': url,
                        'headers' : headers,
                        'customHeaders' : customHeaders,
                        'defaultPayload': defaultPayload,
                        'webhookType': webhookType,
                }
                return self.__http_post(url, data)

        # Get all Metric Monitors
        # https://api.jp.sumologic.com/docs/#operation/getMonitors
        def get_monitors(self):
                url = self.base_url + "/v2/metrics/alerts/monitors"
                return self.__http_get(url)['data']

        # Create new Metric Monitor
        # https://api.jp.sumologic.com/docs/#operation/createMonitor
        def create_monitor(self, name, description, isDisabled, alertQueries, queriesTimeRange, timeZone, monitorRules, muteStatus, chartSettings):
                url = self.base_url + "/v2/metrics/alerts/monitors"
                data = {
                        'name': name,
                        'description': description,
                        'isDisabled': isDisabled,
                        'alertQueries': alertQueries,
                        'queriesTimeRange': queriesTimeRange,
                        'timeZone': timeZone,
                        'monitorRules': monitorRules,
                        'muteStatus': muteStatus,
                        'chartSettings': chartSettings,
                }
                return self.__http_post(url, data)

        # Get all Roles
        # https://api.jp.sumologic.com/docs/#operation/listRoles
        def get_roles(self):
                url = self.base_url + "/v1beta/roles"
                return self.__http_get(url)['data']

        # Get the Role
        # https://api.jp.sumologic.com/docs/#operation/getRole
        def get_role(self, id):
                url = self.base_url + "/v1beta/roles/" + id
                return self.__http_get(url)

        # Create new Role
        # https://api.jp.sumologic.com/docs/#operation/createRole
        def create_role(self, name, description, filterPredicate, users, capabilities):
                url = self.base_url + "/v1beta/roles"
                data = {
                        'name': name,
                        'description': description,
                        'filterPredicate': filterPredicate,
                        'users': users,
                        'capabilities': capabilities,
                }
                return self.__http_post(url, data)

        # Get all Users
        # https://api.jp.sumologic.com/docs/#operation/listUsers
        def get_users(self):
                url = self.base_url + "/v1beta/users"
                return self.__http_get(url)['data']

        # Create new User
        # https://api.jp.sumologic.com/docs/#operation/createUser
        def create_user(self, firstName, lastName, email, roleIds):
                url = self.base_url + "/v1beta/users"
                data = {
                        'firstName': firstName,
                        'lastName': lastName,
                        'email': email,
                        'roleIds': roleIds,
                }
                return self.__http_post(url, data)

        # Common HTTP GET process
        def __http_get(self, url):
                print('http get from: ' + url)
                req = urllib.request.Request(url, headers=self.__create_header())
                with urllib.request.urlopen(req) as res:
                        body = res.read()
                        return json.loads(body)

        # Common HTTP POST process
        def __http_post(self, url, data):
                json_str = json.dumps(data)
                post = json_str.encode('utf-8')
                print('http post to: ' + url)
                print('http post data: ' + json_str)
                req = urllib.request.Request(url, data=post, method='POST', headers=self.__create_header())
                with urllib.request.urlopen(req) as res:
                        body = res.read()
                        return json.loads(body)

        # Create HTTP request header
        def __create_header(self):
                basic = base64.b64encode('{}:{}'.format(self.access_id, self.access_key).encode('utf-8'))
                return { "Authorization": "Basic " + basic.decode('utf-8'), "Content-Type": "application/json" }

# Call main process method
if __name__=='__main__':
    main()
