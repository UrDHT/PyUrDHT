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

    def join(self,bootStraps):
        #seek for insertion point
        found_peers = set(bootStraps)
        best_parent = peer
        new_best = None
        while while new_best is not None and best_parent.id != new_best.id: #comparison on remoteids?
            new_best = self.network.seek(best_parent,self.id)
            found_peers.add(new_best)
        inital_peers = self.network.getPeers(best_parent)
        for p in inital_peers:
            found_peers.add(p)
        with self.peersLock:
            self.short_peers = list(found_peers)
        self.maintenance_thread.start()
        return True

    def shutdown(self):
        self.maintenance_thread.running = False
        #sanity check the following
        with self.maintenance_thread.runningLock:
            pass
        return True

    def doIOwn(self,id):
        loc = space.id_to_point(id)
        with self.peersLock:
            bestloc = space.getClosest(self.seekCanidates)
        return bestloc == self.loc

    def seek(self,id):
        loc = space.id_to_point(id)
        with self.peersLock:
            bestloc = space.getClosest(self.seekCanidates)
            peer = self.loc2peerTable[bestloc]
        return peer

    def getPeers(self):
        with self.peersLock:
            return = self.short_peers[:] + self.long_peers[:]

    def getNotified(self,origin):
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
                #"Notify all my short peers"
                peers_2_keep = []
                with self.parent.peersLock:
                    peers_2_notify = self.parent.short_peers[:]+self.parent.long_peers[:]
                for p in peers_2_notify:
                    if self.parent.network.notify(p,self.parent.info):
                        peers_2_keep.add(p)
                    #throw away nodes I cannot notify.
                time.sleep(5)# essentially the maintaince cycle period

                #"Re-evaluate my peerlist"
                with self.parent.notifiedLock:
                    peers_2_keep += self.parent.notified_me
                    self.parent.notified_me = []
                points = []
                locdict = {}
                for p in set(peers_2_keep):
                    l = space.id_to_point(p.id)
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


            
            