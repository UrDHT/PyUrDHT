"""

This file describes the DHT Logic class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/DHT_Logic.md


"""

"""
# DHT Logic Module

This module is the most complex and is close to being a god object for the project.
Most refinement and modifications required for re-purposing will happen here.

The DHT Logic exposes:

- seek(id) -> return a good forward peer for an id
- getPeers() -> return my current list of 1 hop peers
- getNotified(origin) -> notify me that origin exists
- DoIOwn(id) -> returns True iff I think I am responsible for an address.

The DHT Logic Depends On:

- Network Component: Allows communication with other nodes
    - Seek(remote,id) 
    - GetPeers(remote)
    - Notify(remote,origin)


DHT logic can be internally separated into two parts:
    - Reactive Logic:
        - dealing with queries
        - Has a dedicated worker, processes requests as fast as possible
    - Periodic Logic:
        - deals with maintenance
        - essentially an infinite loop with sleeps.

# TODO:
    - Decide on a good method for dealing with bad peers!!!!!

## Reactive Logic:
 Dealing with a reactive query should work as follows:
 ```
    get read lock on peerInfo
    copy needed peerInfo into local memory
    release read lock on peerInfo
    do required computation generally just a "findmax"
    return value
```

## Periodic Logic:
```
    do while running:
        get read lock on peerInfo
        make local copy
        release read lock on peerInfo
        notify all peers
        sleep for a bit
        get read lock on new_candidates
        make a local copy
        release read lock on new_candidates
        new_peerlist = pick_new_peerlist(peerInfo_copy + new_candidates_copy)
        get write lock on peerInfo
        write new_peerlist over peerInfo
        release write lock on peerInfo
        sleep for a bit

```

"""

from util import PeerInfo #might not be needed if all instantiations happen other places
import EuclidianSpaceMath as space

import threading
import queue
import time

MAX_LONGPEERS = 200
MIN_SHORTPEERS = 10
MAINTENANCE_SLEEP_PERIOD = 10 #set a periodic sleep of 10s on maintenance



class DHTLogic(object):
    def __init__(self, peerInfo):
        self.network = None
        self.shortPeers = []
        self.longPeers = []
        self.seekCandidates = []
        self.notifiedMe = []
        self.loc2PeerTable = {}
        self.info = peerInfo
        self.loc = space.idToPoint(2, self.info.id)
        self.maintenanceThread = None
        self.peersLock = threading.Lock()
        self.notifiedLock = threading.Lock()
        self.mode = "OFFLINE" #replace with enum?

    def setup(self, network):
        self.network = network
        self.maintenanceThread= DHTMaintenceWorker(self)
        return True

    def join(self,peers):
        #seek for insertion point
        if peers:
            print("Joining Network")
            found_peers = set(peers)
            best_parent = peers[0]
            new_best = None
            while new_best is None or best_parent.id != new_best.id: #comparison on remoteids?
                new_best = self.network.seek(best_parent,self.info.id)
                found_peers.add(new_best)
                best_parent = new_best
            inital_peers = self.network.getPeers(best_parent)
            if inital_peers:
                for p in inital_peers:
                    found_peers.add(p)
            with self.peersLock:
                self.shortPeers = list(found_peers)
            print("joined with:",list(found_peers))
            #print("done join, staring worker")
        self.maintenanceThread.start()
        return True

    def shutdown(self):
        self.maintenanceThread.running = False
        #sanity check the following
        with self.maintenanceThread.runningLock:
            pass
        return True

    def doIOwn(self,id):
        return self.seek(id) == self.loc

    def seek(self,id):
        loc = space.idToPoint(2,id)
        candidates = None
        with self.peersLock:
            candidates = self.seekCandidates
        if len(candidates) ==0:
            return self.info
        bestLoc = space.getClosest(loc,candidates)
        peer = self.loc2PeerTable[bestLoc]
        return peer

    def getPeers(self):
        with self.peersLock:
            return self.shortPeers[:] + self.longPeers[:]

    def getNotified(self,origin):
        #print("GOT NOTIFIED",origin)
        with self.notifiedLock:
            self.notifiedMe.append(origin)
        return True


class DHTMaintenceWorker(threading.Thread):
    def __init__(self,parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.running = True
        self.runningLock = threading.Lock()

    def run(self):
        with self.runningLock:

            peerCandidateSet = set()
            while self.running:
                print("short",self.parent.shortPeers)
                #print("myinfo",self.parent.info)
                #print("Worker Tick Start")
                #"Notify all my short peers"
                with self.parent.peersLock:
                    #print("got peer lock")
                    peerCandidateSet.update( set(self.parent.shortPeers[:]+self.parent.longPeers[:]))

                
                print(peerCandidateSet)

                peerCandidateSet = set(filter(self.parent.info.__ne__, peerCandidateSet))
                assert(self.parent.info not in peerCandidateSet)
                #print("thinking")
                #"Re-evaluate my peerlist"
                with self.parent.notifiedLock:
                    peerCandidateSet.update(set(self.parent.notifiedMe))
                    self.parent.notifiedMe = []

                

                for p in set(peerCandidateSet): #Cull anybody who fails a ping
                    if not self.parent.network.ping(p) == True:
                        peerCandidateSet.remove(p)
                    #TODO: make parallel

                points = []
                locDict = {}

                #print(peers_2_keep)
                for p in set(peerCandidateSet):
                    l = space.idToPoint(2,p.id)
                    points.append(l)
                    locDict[l] = p
                locDict[self.parent.loc] = self.parent.info
                newShortLocsList = space.getDelaunayPeers(points,self.parent.loc)
                newShortPeersList = [locDict[x] for x in newShortLocsList]
                leftoversList = list(peerCandidateSet-set(newShortPeersList))

                if len(newShortPeersList)<MIN_SHORTPEERS and len(leftoversList)>0:
                    leftoverLocsList = list(set(points)-set(newShortLocsList))
                    sortedLeftoverLocsList = sorted(leftoverLocsList)
                    needed = min((len(leftoversList),MIN_SHORTPEERS))
                    newShortPeerLocsList = sortedLeftoverLocsList[:needed]
                    newShortPeersList += [locDict[x] for x in newShortPeerLocsList]
                    if needed < len(leftoversList):
                        leftoversList = [locDict[x] for x in sortedLeftoverLocsList[needed:]]
                if len(leftoversList) > MAX_LONGPEERS:
                    leftoversList = random.sample(leftoversList,MAX_LONGPEERS)



                with self.parent.peersLock:
                    self.parent.shortPeers = newShortPeersList
                    self.parent.longPeers = leftoversList
                    self.parent.seekCandidates = points + [self.parent.loc]
                    self.parent.loc2PeerTable = locDict

                for p in newShortPeersList:
                    self.parent.network.notify(p,self.parent.info)
                    peerCandidateSet.update(set(self.parent.network.getPeers(p)))
                    #TODO make parallel

                time.sleep(MAINTENANCE_SLEEP_PERIOD)
