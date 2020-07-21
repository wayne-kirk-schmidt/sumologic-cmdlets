### search_metrics ###

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

### search_metrics ###
