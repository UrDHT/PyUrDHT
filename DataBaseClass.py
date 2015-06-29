"""

This file describes the Database class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Database.md



"""

import time

class DataBase(object):
    def __init__(self):
        self.records = {}
        self.streams = {}
    def setup(self):
        pass
    def shutdown(self):
        pass
    def get(self,id):
        try:
            return self.records[id]
        except:
            return None
    def store(self,id,val):
        self.records[id] = val

    def post(self,id, val):
        val = val
        if id in self.streams.keys():
            self.streams[id].append((time.time(),val))
        else:
            self.streams[id]=[(time.time(),val)]
    def poll(self, id, t):
        try:
            return [x for x in filter(lambda x: x[0]>t,self.streams[id])]
        except:
            return []

    def recordList(self):
        return self.records.keys()
    
