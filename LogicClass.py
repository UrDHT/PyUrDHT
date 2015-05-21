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
    get read lock on peerinfo
    copy needed peerinfo into local memory
    release read lock on peerinfo
    do required computation generally just a "findmax"
    return value
```

## Periodic Logic:
```
    do while running:
        get read lock on peerinfo
        make local copy
        release read lock on peerinfo
        notify all peers
        sleep for a bit
        get read lock on new_canidates
        make a local copy
        release read lock on new_canidates
        new_peerlist = pick_new_peerlist(peerinfo_copy + new_canidates_copy)
        get write lock on peerinfo
        write new_peerlist over peerinfo
        release write lock on peerinfo
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



class DHTLogic(object):
    def __init__(self, peerinfo):
        self.network = None
        self.short_peers = []
        self.long_peers = []
        self.seekCanidates = []
        self.notified_me = []
        self.loc2peerTable = {}
        self.info = peerinfo
        self.loc = space.id_to_point(2, self.info.id)
        self.maintenance_thread = None
        self.peersLock = threading.Lock()
        self.notifiedLock = threading.Lock()
        self.mode = "OFFLINE" #replace with enum?

    def setup(self, network):
        self.network = network
        self.maintenance_thread= DHTMaintenceWorker(self)
        return True

    def join(self,peer):
        #seek for insertion point
        found_peers = set([peer])
        best_parent = peer
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
            self.short_peers = list(found_peers)
        #print("done join, staring worker")
        self.maintenance_thread.start()
        return True

    def shutdown(self):
        self.maintenance_thread.running = False
        #sanity check the following
        with self.maintenance_thread.runningLock:
            pass
        return True

    def doIOwn(self,id):
        loc = space.id_to_point(2,id)

        with self.peersLock:
            if len(self.seekCanidates) == 0:
                return True 
            bestloc = space.getClosest(loc,self.seekCanidates+[self.loc])
        return bestloc == self.loc

    def seek(self,id):
        if(self.doIOwn(id)):
            return self.info

        loc = space.id_to_point(2,id)

        with self.peersLock:
            if len(self.seekCanidates) == 0:
                return self.info 
            bestloc = space.getClosest(loc,self.seekCanidates)
            peer = self.loc2peerTable[bestloc]
        return peer

    def getPeers(self):
        with self.peersLock:
            return self.short_peers[:] + self.long_peers[:]

    def getNotified(self,origin):
        #print("GOT NOTIFIED",origin)
        with self.notifiedLock:
            self.notified_me.append(origin)
        return True


class DHTMaintenceWorker(threading.Thread):
    def __init__(self,parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.running = True
        self.runningLock = threading.Lock()

    def run(self):
        with self.runningLock:

            peers_2_notify = None
            while self.running:
                #print("myinfo",self.parent.info)
                #print("Worker Tick Start")
                #"Notify all my short peers"
                peers_2_keep = []
                with self.parent.peersLock:
                    #print("got peer lock")
                    peers_2_notify = self.parent.short_peers[:]+self.parent.long_peers[:]

                done = False
                while not done:
                    done = True
                    for p in peers_2_notify:
                        if p == self.parent.info:
                            peers_2_notify.remove(p)
                            done = False
                            print("Removed Myself!")
                for p in peers_2_notify:
                    #print("notifying ",p)
                    if self.parent.network.notify(p,self.parent.info):
                        hop_peers = self.parent.network.getPeers(p)
                        if len(hop_peers) > 0:
                            for hop_p in hop_peers:
                                peers_2_keep.append(hop_p)
                        peers_2_keep.append(p)
                    #print("done notifying ",p)
                    #throw away nodes I cannot notify.
                #print("Sleeping")
                time.sleep(5)# essentially the maintaince cycle period
                #print("thinking")
                #"Re-evaluate my peerlist"
                with self.parent.notifiedLock:
                    peers_2_keep += self.parent.notified_me
                    self.parent.notified_me = []
                points = []
                locdict = {}
                done = False
                while not done:
                    done = True
                    for p in peers_2_keep:
                        if p == self.parent.info:
                            peers_2_keep.remove(p)
                            done = False
                            print("Removed Myself!")
                #print(peers_2_keep)
                for p in set(peers_2_keep):
                    l = space.id_to_point(2,p.id)
                    points.append(l)
                    locdict[l] = p
                new_short_locs = space.getDelaunayPeers(points,self.parent.loc)
                new_short_peers = [locdict[x] for x in new_short_locs]
                leftovers = list(set(peers_2_keep)-set(new_short_peers))
                with self.parent.peersLock:
                    self.parent.short_peers = new_short_peers
                    self.parent.long_peers = leftovers
                    self.parent.seekCanidates = points
                    self.parent.loc2peerTable = locdict
                    #print("SHORT",self.parent.short_peers)
                    #print("LONG",self.parent.long_peers)
                    #print("SELF",)
            