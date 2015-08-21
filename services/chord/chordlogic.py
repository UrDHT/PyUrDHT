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
        return """{"id":"%s", "addr":"%s", "loc":[%f,%f]}""" % \
            (self.id, self.addr, self.loc[0], self.loc[1])

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
        self.key = key
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

            patron_peer = random.choice(peers)
            best_parent = patron_peer
            new_best = None
            inital_peers = None
            try:
                while new_best is None or best_parent.id != new_best.id: #comparison on remoteids?
                    new_best = self.network.seek(self.key, best_parent, self.info.id)
                    found_peers.add(new_best)
                    best_parent = new_best
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

    def doIOwn(self,key):
        """
        Looks to see if I own some key.
        If seek returns myself, then I'm the closest
        """
        target = 
    

    #TODO MAKE SURE THIS ACTUALLY WORKS
    def seek(self, key):

        loc = space.idToPoint(key)
        candidates =  None
        with self.peersLock:
            candidates = self.succList[:] + self.longPeers[:]
        if len(candidates) == 0:
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
            return self.succList[:] +  self.predList[:]  + self.longPeers[:]



    def getNotified(self, origin):
        with self.notifiedLock:
            self.notifiedMe.append(origin)
        return True

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

    def stabilize(self):
        pass

    def notify(self):
        pass

    def rectify(self):
        pass
