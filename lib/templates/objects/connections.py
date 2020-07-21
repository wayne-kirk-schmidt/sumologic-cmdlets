### connections ###

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

### connections ###
