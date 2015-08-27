import chordspacemath as space
import threading
import random

class DialFailed(Exception):
    pass

class PeerInfo(object):

    """
        Peerinfo does not actually do much
        I might just reduce it to a 2-tuple

        right now UrDHT is not enforcing a mapping of hashIDs to servers
    """

    def __init__(self, hashID, addr, loc):
        """
            hashID is a string encoded in multihash format
            addr is whatever the network module needs to connect
        """
        self.id = hashID
        self.addr = addr
        self.loc = loc

    def __str__(self):
        return """{"id":"%s", "addr":"%s", "loc":"%s"}""" % \
            (self.id, self.addr, self.loc)

    def __hash__(self):
        return hash((hash(self.id), hash(self.addr)))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return str(self)


class ChordLogic(object):
    """docstring for ChordLogic"""
    def __init__(self, peerinfo, key):
        self.network = None
        self.database = None
        self.key = key      #TODO Rename key
        self.predecessor = None
        self.succList = []
        self.shortPeers = [self.predecessor, self.succList]
        self.longPeers = []
        self.seekCandidates = []
        self.notifiedMe = []
        self.locPeerDict = {}
        self.info = peerinfo
        if peerinfo.loc is None:
            self.loc = space.idToPoint(2, self.info.id)
            self.info.loc = self.loc
        else:
            self.loc = peerinfo.loc
        self.janitorThread = None
        self.peersLock = threading.Lock()
        self.notifiedLock = threading.Lock()
        #TODO: MOAR LOCKS

    def setup(self, network, database):
        self.network = network
        self.database =  database
        self.janitorThread =  ChordJanitor(self)

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

    #TODO: Reimplement chordlike-join
    def join(self, peers):
        """
        In this version of join, we are either provided our peers
        from the lookup, or we do it ourselves.
        """
        if peers:
            print("Joining Network")
            found_peers = set(peers)

            # Assuming we use a bootstrap list,
            # we shouldn't always select the first.
            # Bad load balancing karma
            patron_peer = random.choice(peers)
            best_parent = patron_peer
            new_best = None
            inital_peers = None
            try:
                while new_best is None or best_parent.id != new_best.id: #comparison on remoteids?
                    new_best = self.network.seek(self.key, best_parent, self.info.id)
                    found_peers.add(new_best)
                    best_parent = new_best
                inital_peers = self.network.getSuccessors(self.key, best_parent)
            except DialFailed:
                peers.remove(patron_peer)
                return self.join(peers)
            if inital_peers:
                for p in inital_peers:
                    found_peers.add(p)
            with self.peersLock:
                self.succList=[best_parent] + list(found_peers)[:-1]
            print("joined with:", list(found_peers))
            ##print("done join, staring worker")
        self.janitorThread.start()
        return True

    def doIOwn(self,key):
        """
        Looks to see if I own some key.
        If seek returns myself, then I'm the closest
        """
        with self.peersLock:
            point = space.idToPoint(key)
            return space.isPointBetweenRightInclusive(point, self.predecessor.loc, self.loc)

    def doesMySuccessorOwn(self,key):
        """
        Does my successor own this key
        """
        with self.peersLock:
            point = space.idToPoint(key)
            return space.isPointBetweenRightInclusive(point, self.loc, self.succList[0].loc)


    #TODO MAKE SURE THIS ACTUALLY WORKS
    def seek(self, key):

        if self.doIOwn(key):
            return self.info
        if self.doesMySuccessorOwn(key):
            # do I need a lock?
            return self.succList[0]
        loc = space.idToPoint(key)
        candidates =  None
        with self.peersLock:
            candidates = self.succList[:] + self.longPeers[:]
        if len(candidates) == 0:
            print("Explative Deleted, this node is all alone!")
            return self.info # We have issues
        bestLoc = space.getClosest(loc, candidates)
        peer = self.locPeerDict[bestLoc]
        return peer

    def getPeers(self):
        """
        Returns a list of all the peers I know.
        In otherwords, my neighbors and my shortcuts
        """
        with self.peersLock:
            return self.succList[:] +  [self.predecessor] + self.longPeers[:]

    def getSuccessors(self):
        with self.peersLocks:
            return self.succList[:]

    def getPredecessor(self):
        with self.peersLocks:
            return [self.predecessor]

    def getNotified(self, origin):
        with self.notifiedLock:
            self.notifiedMe.append(origin)
        return True


    def stabilize(self):
        while self.succList:   
            newSucc =  self.succList[0]
            newList = []
            predOfSucc = self.info
            try:
                predOfSucc = self.network.getPredecessor(self.key, self.succList[0])
                newList = newList = self.network.getSuccessors(self.key, self.succList[0])
            except DialFailed:  # Our successor is dead, long live the new successor
                if self.succList:
                    with self.peersLock:
                        self.succList = self.succList[1:]
                continue

            if space.isPointBetween(predOfSucc.loc, self.loc, self.succList[0].loc):
                newSucc = predOfSucc
                try:
                    newList = self.network.getSuccessors(self.key, predOfSucc)
                except DialFailed:  # if we can't communicate with predOfSucc
                    break
            with self.peersLock:
                self.succList = [newSucc] + newList
                break

    def notify(self):  #if notify fails, ignore and let stabilize handle it
        try:
            self.network.notify(self.key, self.succList[0], self.info)
        except:
            print("failed to nofify", self.succList[0])

    def rectify(self):
        candidates = [] 
        
        # empty the notified list
        with self.notifiedLock:
            candidates = self.notifiedMe[:]
            self.notifiedMe = [] 
        

        for p in candidates:
            #try pinging the notifier first
            try: 
                self.network.ping(self.key, p)
            except:  #do nothing, skip
                continue
            
            #make sure the current pred is still alive
            try:
                self.network.ping(self.key, self.predecessor)
            except:  # well, we have to replace it now, don't we
                with self.peersLock:
                    self.predecessor = p 
                    continue
            with self.peersLock:  #TODO WHERE SHOULD THE LOCK GO?
                if self.predecessor is None:
                    self.predecessor = p
                elif space.isPointBetween(p.loc, self.predecessor.loc, self.loc):
                    self.predecessor = p 


    def createDict(self):
        pass

    def onResponsibilityChange(self):
        pass

class ChordJanitor(object):
    def __init__(self, parent):
        """
        Initialized the janitor with parent as the node that created it.
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.running = True
        self.runningLock = threading.Lock()


    """
    step 1: stabilize
    step 1.5: update sucessorlist
    step 2: notify, which causes notified member to rectify
    """

