import chordspacemath as space
import threading
import time
import random
from chordnetwork import DialFailed

# TODO Remove this node should be a forged notify

MAX_LONGPEERS = space.KEYSIZE
MAX_SUCCESSORS = 4  # Number chosen at random, see https://xkcd.com/221/
MAINTENANCE_SLEEP_PERIOD = 10  # set a periodic sleep of 10s on maintenance


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
        self.key = key      # TODO Rename key
        self.predecessor = None
        self.succList = []
        self.shortPeers = [self.predecessor, self.succList]
        self.longPeers = []
        # self.seekCandidates = []
        self.notifiedMe = []
        self.info = peerinfo
        if peerinfo.loc is None:
            self.loc = space.idToPoint(self.info.id)
            self.info.loc = self.loc
        else:
            self.loc = peerinfo.loc
        self.janitorThread = None
        self.shortcutThread = None
        self.peersLock = threading.RLock()
        self.notifiedLock = threading.RLock()
        # TODO: MOAR LOCKS

    def setup(self, network, database):
        """
        Setup just connects Logic to the other components 
        and initializes, but doens't start, the janitors
        """
        self.network = network
        self.database = database
        self.janitorThread = ChordJanitor(self)
        self.shortcutThread =  ShortcutJanitor(self)

    def shutdown(self):
        """
        Kills the maintenance thread, waits for the thread to realize it.
        Returns True when done
        """
        self.janitorThread.running = False
        self.shortcutThread.running = False
        with self.janitorThread.runningLock:  # sanity check
            pass
        with self.shortcutThread.runningLock:
            pass
        return True

    def join(self, peers):
        """
        Using a list of peers, we ask the network to find our successor
        We connect to them and initialize the janitors 
        """

        if peers:
            print("Joining Network")

            # Assuming we use a bootstrap list,
            # we shouldn't always select the first.
            # Bad load balancing karma
            patronPeer = random.choice(peers)

            # bestParent is the best we found so far,
            # newBest is the one we've found this round
            bestParent = patronPeer
            newBest = None
            parentSuccessors = None
            
            # while it's the first round or we've found something closer   
            try:
                while newBest is None or bestParent.id != newBest.id:
                    # we found something closer, that's now the bestParent
                    if newBest is not None:
                        bestParent = newBest
                    # find next closest node
                    newBest = self.network.seek(self.key, bestParent, self.info.id)
                parentSuccessors = self.network.getSuccessors(self.key, bestParent) 
            except DialFailed: # TODO we could do this more elegantly
                peers.remove(patronPeer)
                return self.join(peers)

            # create the successor list
            with self.peersLock:
                self.succList = [bestParent] + parentSuccessors

            # If our successor list is now bigger than the max, trim it
            if self.succList > MAX_SUCCESSORS:
                with self.peersLock:
                    self.succList = self.succList[:MAX_SUCCESSORS]

            print("joined with:", bestParent)

        self.janitorThread.start()
        self.shortcutThread.start()
        return True

    def doIOwn(self, key):
        """
        Looks to see if I own some key.
        If seek returns myself, then I'm the closest
        """
        point = space.idToPoint(key)
        return space.isPointBetweenRightInclusive(point, self.predecessor.loc, self.loc)

    def doIOwnPoint(self, point):
        """
        Looks to see if I own some point.
        If seek returns myself, then I'm the closest
        """
        return space.isPointBetweenRightInclusive(point, self.predecessor.loc, self.loc)

    def doesMySuccessorOwn(self, key):
        """
        Does my successor own this key
        """
        point = space.idToPoint(key)
        return space.isPointBetweenRightInclusive(point, self.loc, self.succList[0].loc)

    def doesMySuccessorOwnPoint(self, point):
        """
        Does my successor own this point
        """
        return space.isPointBetweenRightInclusive(point, self.loc, self.succList[0].loc)

    def seek(self, key):
        """
        Returns the node I know either responsible for or closest to key
        """
        loc = space.idToPoint(key)
        return self.seekPoint(loc)

    def seekPoint(self, point):  # TODO MAKE SURE THIS ACTUALLY WORKS
        """
        Returns the node I know either responsible for or closest to key
        """
        if self.doIOwnPoint(point):
            return self.info
        if self.doesMySuccessorOwnPoint(point):
            return self.succList[0]
        candidates = None
        with self.peersLock:
            candidates = self.longPeers[:] + self.succList[:]
        if len(candidates) == 0:
            print("Explitive Deleted, this node is all alone!")
            return self.info  # We have issues

        # TODO: if nothing works, look here, also improvement can be done here.
        closestPeer = space.getClosest(point, list(set(candidates)))  
        return closestPeer

    def lookup(self, key):
        """
        Iterative lookup of key

        key:  a multihash key
        returns -> node responsible for key
        """
        loc = space.idToPoint(key)
        return self.lookupPoint(loc)

    def lookupPoint(self, point):
        """
        Iterative lookup of a point

        point - an int
        returns -> node responsible for key
        """
        if self.doIOwnPoint(point):
            return self.info
        if self.doesMySuccessorOwnPoint(point):
            return self.succList[0]

        
        # run seek on myself
        best = self.seekPoint(point)
        
        providerOfBest = self.info  # The guy who gave me who best currently is
        newBest = None
        
        while newBest is None or newBest.loc != best.loc:
            if newBest is not None:
                providerOfBest = best
                best = newBest
            try:
                newBest = self.network.seekPoint(self.key, best, point)

            # if an error, we try to roll it back a single step
            # if that fails too, we fail completely
            except:
                if best == self.info:
                    raise DialFailed
                
                else:                    
                    # TODO THIS STRATEGY WILL STOP WORKING AND NEED A SLEEP IF WE SWITCH TO FORGING NOTIFIES
                    self.network.removeThisNode(self.key, providerOfBest, best)
                    best = providerOfBest
                    providerOfBest = self.info
                    newBest = None
        return best

    def getPeers(self):
        """
        Returns a list of all the peers I know.
        In otherwords, my neighbors and my shortcuts
        """
        with self.peersLock:
            return self.succList[:] + [self.predecessor] + self.longPeers[:]

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

    def removeThisNode(self, badNode):
        """
        Blatant security hole
        """
        with self.peersLock:
            self.succList.remove(badNode)
            self.longPeers.remove(badNode)

    def stabilize(self):
        """
        Stabilize checks the successor's predecessor, predOfSucc.

        If predOfSucc is better than the current successor
        predOfSucc become the head of the new succList.

        Either way, succList is updated
        """



        while len(self.succList) != 0:    # So long as we have a potential successor
            # initialize the new lists
            newSucc = self.succList[0]
            newList = []
            predOfSucc = self.info

            # get our successor's predeccessor
            # if fail, remove the head of succList and retry the loop
            try:
                predOfSucc = self.network.getPredecessor(self.key, self.succList[0])
                newList = self.network.getSuccessors(self.key, self.succList[0])
            except DialFailed:  # Our successor is dead ...
                if self.succList:
                    with self.peersLock:  # ... long live the new successor
                        self.succList = self.succList[1:]
                continue

            # if our predOfSucc is better, use it
            # if our call fails that means the succ needs to update his pred
            # In that case we use our current successor and his info
            if space.isPointBetween(predOfSucc.loc, self.loc, self.succList[0].loc):
                try:
                    temp = self.network.getSuccessors(self.key, predOfSucc)
                    newList = temp
                except DialFailed:  # if we can't communicate with predOfSucc
                    with self.peersLock:
                        self.succList = [newSucc] + newList
                    # If our successor list is now bigger than the max
                    if self.succList > MAX_SUCCESSORS:
                        with self.peersLock:
                            self.succList = self.succList[:MAX_SUCCESSORS]
                    break
                newSucc = predOfSucc

            # update the successor list
            with self.peersLock:
                self.succList = [newSucc] + newList
            if len(self.succList) > MAX_SUCCESSORS:
                with self.peersLock:
                    self.succList = self.succList[:MAX_SUCCESSORS]
            break

    def notify(self):  # if notify fails, ignore and let stabilize handle it
        """
        notify simples tells the successor I exist
        """
        try:
            self.network.notify(self.key, self.succList[0], self.info)
        except:
            print("failed to nofify", self.succList[0])

    def rectify(self):
        """
        With rectify, a node checks if the predecessor is alive
        Then, we go thru the nodes which notified us to see if
        they're better than our predecessor.

        If so, they replace our predecessor


        TODO: if I'm reading this correctly we will always have a predecessor
        even if it's dead
        """

        candidates = []

        # empty the notified list
        with self.notifiedLock:
            candidates = self.notifiedMe[:]
            self.notifiedMe = []

        predChanged = False
        # try pinging the notifier first, skip if dead
        for p in candidates:
            try:
                self.network.ping(self.key, p)
            except:  # do nothing, skip
                continue

            # make sure the current pred is still alive
            try:
                self.network.ping(self.key, self.predecessor)
            except:  # well, we have to replace it now, don't we
                with self.peersLock:
                    self.predecessor = p
                predChanged = True
                continue

            # if my pred is None, replace it
            if self.predecessor is None:
                with self.peersLock:
                    self.predecessor = p
                predChanged = True
            # if my notifier is closer, it's my new pred
            elif space.isPointBetween(p.loc, self.predecessor.loc, self.loc):
                with self.peersLock:
                    self.predecessor = p
                predChanged = True
        return predChanged

    def onResponsibilityChange(self):
        # TODO:  refine so we don't have to keep backing up stuff

        # get the keys I am responsible for
        recordKeys = list(filter(self.doIOwn, self.database.getRecords()))
        
        # get my successors 
        mySuccessors = []
        with self.peersLock:
            mySuccessors = self.sucessorlist
        
        # for each key, get the value associated with it and 
        # store it at my buddies
        for key in recordKeys:
            value =  self.database.get(key)
            for s in mySuccessors:
                try:
                    self.network.store(self.key, s, key, value)
                except Exception as e:
                    print(e)
                    continue


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

    def run(self):
        with self.runningLock:
            while self.running:
                self.cleanup()
                time.sleep(MAINTENANCE_SLEEP_PERIOD)

    def cleanup(self):
        self.parent.stablize()
        self.parent.notify()
        changed = self.parent.rectify()
        if changed:
            self.parent.onResponsibilityChange()


class ShortcutJanitor():
    def __init__(self, parent):
        """
        Initialized the janitor with parent as the node that created it.
        """
        threading.Thread.__init__(self, parent)
        self.parent = parent
        self.running = True
        self.runningLock = threading.Lock()

    def run(self):
        with self.runningLock:
            index = MAX_LONGPEERS - 1
            while self.running:
                self.cleanup(index)
                index -= 1
                if index < 0:
                    index = MAX_LONGPEERS - 1
                time.sleep(MAINTENANCE_SLEEP_PERIOD / 4.0)

    def cleanup(self, index):
        replacementNode = self.findShortcut(index)
        if len(self.parent.longPeers) == MAX_LONGPEERS:
            with self.parent.peersLock:
                self.parent.longPeers[(MAX_LONGPEERS - 1) - index] = replacementNode
        else:
            with self.parent.peersLock:
                self.parent.longPeers.append(replacementNode)

    def findShortcut(self, index):
        target = (self.parent.loc + (2 ** index)) % (2 ** MAX_LONGPEERS)
        bestShortcut = self.parent.lookupPoint(target)
        return bestShortcut
