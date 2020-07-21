### users ###

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

### users ###
