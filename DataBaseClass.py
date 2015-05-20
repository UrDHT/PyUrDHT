"""

This file describes the Database class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Database.md



"""


class DataBase(object):
    def __init__(self):
        self.records = {}
    def setup(self):
        pass
    def shutdown(self):
        pass
    def get(self,id):
        try:
            return self.records[id]
        except:
            return None
    def put(self,id,val):
        self.records[id] = val