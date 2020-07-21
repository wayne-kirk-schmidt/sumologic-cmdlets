### fers ###

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

### fers ###
