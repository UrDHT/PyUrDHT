"""

This file describes the Database class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Database.md

"""

import time, sys, os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname("../../vendored/"), os.path.pardir )))
from vendored import pymultihash as MultiHash

DEFAULT_BLOCK_SIZE = 1024 * 8 # bytes
MAX_BLOCK_SIZE = float("inf")


class DataBase(object):

    def __init__(self):
        self.records = {}
        self.streams = {}

    def setup(self):
        pass

    def shutdown(self):
        pass

    def get(self, id):
        try:
            return self.records[id]
        except:
            return None

    def store(self, id, val):
        self.records[id] = val

    def storePiece(self, pieceID, piece):
        self.records[id] = piece

    def post(self, id, val):
        val = val
        if id in self.streams.keys():
            self.streams[id].append((time.time(), val))
        else:
            self.streams[id] = [(time.time(), val)]

    def poll(self, id, t):
        try:
            return [x for x in filter(lambda x: x[0] > t, self.streams[id])]
        except:
            return []

    def getRecords(self):
        return self.records.keys()


class KeyFile(object):

    def __init__(self, primaryKey):
        self.key = primaryKey
        self.chunkKeys = []


class Chunk(object):

    def __init__(self, chunkKey, contents):
        self.key = chunkKey
        self.contents = contents




def makeChunks(filename, chunkGenerator):
    primaryKey =  MultiHash.genHash(filename , 0x12)
    keyfile = KeyFile(primaryKey)
    chunks = []
    for chunk in chunkGenerator(filename):
        keyFile.chunkKeys.append(chunk.key)
        chunks.append(chunk)
    return (keyfile, chunks)
        
def dumbChunk(filename):
    # Creates ONE chunk of all the data
    raw = ""
    with open(filename,'r') as fin:
        raw = fin.read()
    
    fileKey =  MultiHash.genHash(filename, 0x12)
    contentKey = MultiHash.genHash(raw, 0x12)
    print(fileKey)
    print(contentKey)
    
def textChunkGenerator(filename):
    pass
    
    
    
def test():
    dumbChunk("hamlet.txt")



    
if __name__ ==  '__main__':
    test()
