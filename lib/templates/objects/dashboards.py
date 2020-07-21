### dashboards ###
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

### dashboards ###
