    def get_collectors(self, limit=1000, offset=None):
        params = {'limit': limit, 'offset': offset}
        r = self.get('/v1/collectors', params)
        return json.loads(r.text)['collectors']

    def get_collectors_sync(self, limit=1000):
        offset = 0
        results = []
        r = self.get_collectors(limit=limit, offset=offset)
        offset = offset + limit
        results = results + r
        while not(len(r) < limit):
            r = self.get_collectors(limit=limit, offset=offset)
            offset = offset + limit
            results = results + r
        return results

    def collector(self, collector_id):
        r = self.get('/v1/collectors/' + str(collector_id))
        return json.loads(r.text), r.headers['etag']

    def create_collector(self, collector, headers=None):
        return self.post('/v1/collectors', collector, headers)

    def update_collector(self, collector, etag):
        headers = {'If-Match': etag}
        return self.put('/v1/collectors/' + str(collector['collector']['id']), collector, headers)

    def delete_collector(self, collector_id):
        return self.delete('/v1/collectors/' + str(collector_id))

    def sources(self, collector_id, limit=None, offset=None):
        params = {'limit': limit, 'offset': offset}
        r = self.get('/v1/collectors/' + str(collector_id) + '/sources', params)
        return json.loads(r.text)['sources']

    def source(self, collector_id, source_id):
        r = self.get('/v1/collectors/' + str(collector_id) + '/sources/' + str(source_id))
        return json.loads(r.text), r.headers['etag']

    def create_source(self, collector_id, source):
        return self.post('/v1/collectors/' + str(collector_id) + '/sources', source)

    def update_source(self, collector_id, source, etag):
        headers = {'If-Match': etag}
        return self.put('/v1/collectors/' + str(collector_id) + '/sources/' + str(source['source']['id']), source, headers)

    def delete_source(self, collector_id, source_id):
        return self.delete('/v1/collectors/' + str(collector_id) + '/sources/' + str(source_id))

    def dashboards(self, monitors=False):
        params = {'monitors': monitors}
        r = self.get('/v1/dashboards', params)
        return json.loads(r.text)['dashboards']

    def dashboard(self, dashboard_id):
        r = self.get('/v1/dashboards/' + str(dashboard_id))
        return json.loads(r.text)['dashboard']

    def dashboard_data(self, dashboard_id):
        r = self.get('/v1/dashboards/' + str(dashboard_id) + '/data')
        return json.loads(r.text)['dashboardMonitorDatas']

    def search_metrics(self, query, fromTime=None, toTime=None, requestedDataPoints=600, maxDataPoints=800):
        '''Perform a single Sumo metrics query'''
        def millisectimestamp(ts):
            '''Convert UNIX timestamp to milliseconds'''
            if ts > 10**12:
                ts = ts/(10**(len(str(ts))-13))
            else:
                ts = ts*10**(12-len(str(ts)))
            return int(ts)

        data = {'query': [{"query":query, "rowId":"A"}],
                  'startTime': millisectimestamp(fromTime),
                  'endTime': millisectimestamp(toTime),
                  'requestedDataPoints': requestedDataPoints,
                  'maxDataPoints': maxDataPoints}
        r = self.post('/v1/metrics/results', data)
        return json.loads(r.text)

    def create_folder(self, folder_name, parent_id, adminmode=False):
        headers = {'isAdminMode': str(adminmode)}
        data = {'name': str(folder_name), 'parentId': str(parent_id)}
        r = self.post('/v2/content/folders', data, headers=headers)
        return json.loads(r.text)

    def get_folder(self, folder_id, adminmode=False):
        headers = {'isAdminMode': str(adminmode).lower()}
        r = self.get('/v2/content/folders/' + str(folder_id), headers=headers)
        return json.loads(r.text)

    def get_personal_folder(self):
        r = self.get('/v2/content/folders/personal')
        return json.loads(r.text)

    def get_global_folder_job_status(self, job_id):
        r = self.get('/v2/content/folders/global/' + str(job_id) + '/status')
        return json.loads(r.text)

    def get_global_folder(self, adminmode=False):
        headers = {'isAdminMode': str(adminmode).lower()}
        r = self.get('/v2/content/folders/global', headers=headers)
        return json.loads(r.text)

    def get_global_folder_job_result(self, job_id):
        r = self.get('/v2/content/folders/global/' + str(job_id) + '/result')
        return json.loads(r.text)

    def get_global_folder_sync(self, adminmode=False):
        r = self.get_global_folder(adminmode=adminmode)
        job_id = str(r['id'])
        status = self.get_global_folder_job_status(job_id)
        while status['status'] == 'InProgress':
            status = self.get_global_folder_job_status(job_id)
        if status['status'] == 'Success':
            r = self.get_global_folder_job_result(job_id)
            return r
        else:
            return status

    def get_admin_folder_job_status(self, job_id):

        r = self.get('/v2/content/folders/adminRecommended/' + str(job_id) + '/status')
        return json.loads(r.text)

    def get_admin_folder(self, adminmode=False):
        headers = {'isAdminMode': str(adminmode).lower()}
        r = self.get('/v2/content/folders/adminRecommended',  headers=headers)
        return json.loads(r.text)

    def get_admin_folder_job_result(self, job_id):
        r = self.get('/v2/content/folders/adminRecommended/' + str(job_id) + '/result')
        return json.loads(r.text)

    def get_admin_folder_sync(self, adminmode=False):
        r = self.get_admin_folder(adminmode=adminmode)
        job_id = str(r['id'])
        status = self.get_admin_folder_job_status(job_id)
        while status['status'] == 'InProgress':
            status = self.get_admin_folder_job_status(job_id)
        if status['status'] == 'Success':
            r = self.get_admin_folder_job_result(job_id)
            return r
        else:
            return status

    def get_users(self, limit=1000, token=None, sort_by='lastName', email=None):
        params = {'limit': limit, 'token': token, 'sortBy': sort_by, 'email':email }
        r = self.get('/v1/users', params=params)
        return json.loads(r.text)

    def get_user(self, user_id):
        r = self.get('/v1/users/' + str(user_id))
        return json.loads(r.text)

    def create_user(self, first_name, last_name, email, roleIDs):
        data = {'firstName': str(first_name), 'lastName': str(last_name), 'email': str(email), 'roleIds': roleIDs}
        r = self.post('/v1/users', data)
        return json.loads(r.text)

    def get_connections(self, limit=1000, token=''):
        params = {'limit': limit, 'token': token}
        r = self.get('/v1/connections', params=params)
        return json.loads(r.text)

    def get_connections_sync(self, limit=1000):
        token = None
        results = []
        while not(token):
            r = self.get_connections(limit=limit, token=token)
            token = r['next']
            results = results + r['data']
        return results

    def get_fers(self, limit=1000, token=''):
        params = {'limit': limit, 'token': token}
        r = self.get('/v1/extractionRules', params=params)
        return json.loads(r.text)

    def get_fers_sync(self, limit=1000):
        token = None
        results = []
        while True:
            r = self.get_fers(limit=limit, token=token)
            token = r['next']
            results = results + r['data']
            if token is None:
                break
        return results

    def create_fer(self, name, scope, parse_expression, enabled=False):
        data = {'name': name, 'scope': scope, 'parseExpression': parse_expression, 'enabled': str(enabled).lower()}
        r = self.post('/v1/extractionRules', data)
        return json.loads(r.text)

    def get_fer(self, item_id):
        r = self.get('/v1/extractionRules/' + str(item_id))
        return json.loads(r.text)

    def update_fer(self, item_id, name, scope, parse_expression, enabled=False):
        data = {'name': name, 'scope': scope, 'parseExpression': parse_expression, 'enabled': str(enabled).lower()}
        r = self.put('/v1/extractionRules/' + str(item_id), data)
        return json.loads(r.text)

    def delete_fer(self, item_id):
        r = self.delete('/v1/extractionRules/' + str(item_id))
        return r.text
