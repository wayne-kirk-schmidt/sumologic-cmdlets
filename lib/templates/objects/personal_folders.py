### personal_folders ###

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

### personal_folders ###
