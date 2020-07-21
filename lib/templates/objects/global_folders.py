### global_folders ###

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

### global_folders ###
