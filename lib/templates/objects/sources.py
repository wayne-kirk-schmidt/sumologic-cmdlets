### sources ###

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

### sources ###
