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
import HyperbolicSpaceMath as space

import threading
import queue
import time
import random
from errors import *

from threadpool import Threadpool


MAX_LONGPEERS = 200
MIN_SHORTPEERS = 10
MAINTENANCE_SLEEP_PERIOD = 10 #set a periodic sleep of 10s on maintenance

class DHTLogic(object):
    def __init__(self, peerInfo, key):
        """Initializes the node with a PeerInfo object"""
        self.network = None
        self.database = None
        self.key = key
        self.shortPeers = []
        self.longPeers = []
        self.seekCandidates = []
        self.notifiedMe = []
        self.locPeerDict = {}
        self.info = peerInfo
        if peerInfo.loc is None:
            self.loc = space.idToPoint(2, self.info.id)
            self.info.loc = self.loc
        else:
            self.loc = peerInfo.loc
        self.janitorThread = None
        self.peersLock = threading.Lock()
        self.notifiedLock = threading.Lock()

    def setup(self, network, database):
        """
        network: Network object, the means by which the node can communicate.
        After setting network, we can create the Maintenance thread, but not start it
        """
        self.network = network
        self.database = database
        self.janitorThread= DHTJanitor(self)
        return True

    def join(self,peers):
        """
        peers: some list of peers, which are other nodes on the network.
        peers is most likely a list of nodes for bootstrapping, a specific list
        which was included in the config file.

        join joins the network which peers is on.
        We use a random peer from peers to seek for the node currently resonsible for my id
        """

        if peers:
            print("Joining Network")
            found_peers = set(peers)
            # Assuming we use a bootstrap list,
            # we shouldn't always select the first.
            # Bad load balancing karma

            #go ahead and populate the locPeerDict (see bug #77)
            with self.peersLock:
                self.locPeerDict = {x.loc:x for x in found_peers }

            patron_peer = random.choice(peers)
            best_parent = patron_peer
            new_best = None
            inital_peers = None
            try:
                while new_best is None or best_parent.id != new_best.id: #comparison on remoteids?

                    if new_best is not None:
                        best_parent = new_best
                    new_best = self.network.seek(self.key,best_parent,self.info.id)
                    found_peers.add(new_best)

                inital_peers = self.network.getPeers(self.key,best_parent)
            except DialFailed:
                peers.remove(patron_peer)
                return self.join(peers)


            if inital_peers:
                for p in inital_peers:
                    found_peers.add(p)
            with self.peersLock:
                self.shortPeers = list(found_peers)
            print("joined with:",list(found_peers))
            ##print("done join, staring worker")
        self.janitorThread.start()
        return True

    def shutdown(self):
        """
        Kills the maintenance thread, waits for the thread to realize it.
        Returns True when done
        """
        self.janitorThread.running = False
        #sanity check the following
        with self.janitorThread.runningLock:
            pass
        return True

    def doIOwn(self,key):
        """
        Looks to see if I own some key.
        If seek returns myself, then I'm the closest
        """
        return self.seek(key) == self.loc


    #TODO HAVE WE ACTUALLY TESTED SEEK TO MAKE SURE IF I CALL IT AND I SHOULD BE THE ANSWER, IT COMES BACK WITH ME?
    def seek(self,key):
        """
        Answers the question: of the nodes I know, which is the closest to key?
        Key is some key we are looking for.

        Essentially, seek(key) is a single step of a lookup(key) operation.
        Throw seek into a loop and you have iterative lookup!
        """
        loc = space.idToPoint(2, key)
        candidates = None
        with self.peersLock:
            candidates = self.seekCandidates
        if len(candidates) == 0:
            return self.info  # as Toad would say, "I'm the best!"
        bestLoc = space.getClosest(loc, candidates)
        peer = self.locPeerDict[bestLoc]
        return peer

    def getPeers(self):
        """
        Returns a list of all the peers I know.
        In otherwords, my neighbors and my shortcuts
        """
        with self.peersLock:
            return self.shortPeers[:] + self.longPeers[:]

    def getNotified(self, origin):
        """
        A node called has origin has just notified me it exists.

        The purpose of this depends on the DHT.
        Example in Chord: I exist and I think you're my successor.
        """
        ##print("GOT NOTIFIED",origin)
        with self.notifiedLock:
            self.notifiedMe.append(origin)
        return True

    def onResponsibilityChange(self):
        #print("BACKUP IS HAPPENING")
        records = list(filter(self.doIOwn, self.database.getRecords()))
        ##print(records)
        rlocs = list(map(lambda x: space.idToPoint(2, x), records))
        ##print(rlocs)
        lMap = {}
        for l,p in zip(rlocs,records):
            lMap[l]=p
        candidates = None
        with self.peersLock:
            candidates = self.seekCandidates[:]
        if candidates is None:
            return
        candidates.remove(self.loc)
        #print("canidates",candidates)
        if len(candidates) == 0:
            return #im alone, no backups to send
        for loc in rlocs:

            l = lMap[loc]
            bestLoc = space.getClosest(loc, candidates)
            peer = self.locPeerDict[bestLoc]
            value = self.database.get(l)
            #print(loc,l,peer)
            try:
                self.network.store(self.key,peer,l,value)#this backs up existing values, and stores old values on new nodes.
                #print("%s is backed up to %s"%(l,peer))
            except Exception as e:
                print(e)
                continue




class DHTJanitor(threading.Thread):
    """
    DHTJanitor (who I will call janitor from now on) is a thread.
    Like the real life equivalent, our janitor is responsible for cleaning up.

    The messes here are inconsistancies in the DHT topology as a whole, caused
    by churn.
    Now our janitor can't fix the entire network topology by himself,
    but he can clean up the inaccuracies that are relatively local.

    """

    def __init__(self, parent):
        """
        Initialized the janitor with parent as the node that created it.
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.running = True
        self.runningLock = threading.Lock()

    def run(self):
        """
        Starts the thread
        Needs to be split into more methods
        """
        with self.runningLock:
            peerCandidateSet = set()
            while self.running:
                #print("short",self.parent.shortPeers)
                ##print("myinfo",self.parent.info)
                ##print("Worker Tick Start")
                #"Notify all my short peers"
                with self.parent.peersLock:
                    ##print("got peer lock")
                    peerCandidateSet.update( set(self.parent.shortPeers[:]+self.parent.longPeers[:]))


                #print(peerCandidateSet)

                peerCandidateSet = set(filter(self.parent.info.__ne__, peerCandidateSet)) #everyone who is not me
                assert(self.parent.info not in peerCandidateSet) #everyone who is not me
                ##print("thinking")
                #"Re-evaluate my peerlist"
                with self.parent.notifiedLock:  #functionize into handleNotifies
                    peerCandidateSet.update(set(self.parent.notifiedMe))




                def pingCheck(p):
                    if not self.parent.network.ping(self.parent.key,p) == True:
                        peerCandidateSet.remove(p)
                        #print("Ping Failed",p)
                threads = Threadpool(10)
                for x in threads.map(pingCheck,set(peerCandidateSet)):
                    pass

                points = []
                locDict = {}

                ##print(peers_2_keep)
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
                    needed = min((len(leftoversList),MIN_SHORTPEERS-len(newShortPeersList)))
                    newShortPeerLocsList = sortedLeftoverLocsList[:needed]
                    newShortPeersList += [locDict[x] for x in newShortPeerLocsList]
                    if needed < len(leftoversList):
                        leftoversList = [locDict[x] for x in sortedLeftoverLocsList[needed:]]
                if len(leftoversList) > MAX_LONGPEERS:
                    leftoversList = random.sample(leftoversList,MAX_LONGPEERS)






                peerCandidateSet = set()
                def notifyAndGet(p):
                    try:
                        self.parent.network.notify(self.parent.key,p,self.parent.info)
                        newpeers = self.parent.network.getPeers(self.parent.key,p)
                        peerCandidateSet.update(set(newpeers))
                    except DialFailed:
                        #print("DIAL FAILED",p)
                        with self.parent.peersLock:
                            if p in self.parent.shortPeers:
                                self.parent.shortPeers.remove(p)
                            if p in self.parent.longPeers:
                                self.parent.longPeers.remove(p)
                        #with self.parent.notifiedLock:
                        #    self.parent.notifiedMe = []

                threads = Threadpool(10)
                #print("about to map")
                for x in threads.map(notifyAndGet,set(newShortPeersList)):
                    pass
                #print("done mapping")

                trigger_change = False
                with self.parent.peersLock:
                    if self.parent.shortPeers != newShortPeersList:
                        trigger_change = True #consider reducing this to a copy, and compare outside the lock
                    self.parent.shortPeers = newShortPeersList

                    self.parent.longPeers = leftoversList
                    self.parent.seekCandidates = points + [self.parent.loc]
                    self.parent.locPeerDict = locDict
                with self.parent.notifiedLock:
                    self.parent.notifiedMe = []
                if trigger_change or random.random()<0.0:
                    self.parent.onResponsibilityChange()
                time.sleep(MAINTENANCE_SLEEP_PERIOD)
