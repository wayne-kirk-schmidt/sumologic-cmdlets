### collectors ###

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

### collectors ###
