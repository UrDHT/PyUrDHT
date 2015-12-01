import threading


class MapThread(threading.Thread):

    """docstring for MapThread"""

    def __init__(self, parent):
        super(MapThread, threading.Thread).__init__()
        self.parent = parent
        self.jobs = {}

    def startFile(self):
        pass


class ReduceThread(threading.Thread):

    def __init__(self, parent):
        super(ReduceThread, threading.Thread).__init__()
        self.parent = parent
        self.jobs = {}
