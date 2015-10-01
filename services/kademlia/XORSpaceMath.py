import pymultihash as MultiHash

import random

MAXVAL = 2**256

def idToPoint(dim, id):
    """
    We're using a unit space for the position of our nodes.
    The mapping we use is to use the hash ID as the seed to an RNG.
    We should switch to either
    1) A universal RNG
    2) The mapping done by Symphony
    """
    idLong = MultiHash.parseHash(id)
    return tuple([idLong,0])

def distance(p0, p1):
    """Returns the distance from point 1 to point 2?"""
    return int(p0[0]) ^ int(p1[0])

def getDelaunayPeers(candidates, center):
    """
    This builds a bucket structure, and returns peers that fit into kademlia's bucket structure
    """
    bucket_size = 5

    if len(candidates) < bucket_size:
        return candidates
    buckets = {(0, MAXVAL): [center]}
    sortedCandidates = sorted(candidates, key=lambda x: distance(x, center))
    for c in sortedCandidates:
        for r in buckets.keys():
            if c[0] >= r[0] and c[0] < r[1]:
                #mah bucket!
                if(len(buckets[r]) < bucket_size):
                    #I fit in this bucket!
                    buckets[r].append(c)
                else:
                    #I dont fit in this bucket
                    if center in buckets[r]:
                        #this bucket matters!
                        r0 = (r[0], r[0]+(r[1]-r[0])/2)
                        r1 = (r[0]+(r[1]-r[0])/2, r[1])
                        buckets[r0] = []
                        buckets[r1] = []
                        for p in buckets[r]:
                            if p[0] >= r0[0] and p[0] < r0[1]:
                                buckets[r0].append(p)
                            else:
                                buckets[r1].append(p)
                        del buckets[r]
                        if c[0] >= r0[0] and c[0] < r0[1] and len(buckets[r0]) < bucket_size:
                            buckets[r0].append(c)
                        elif c[0] >= r1[0] and c[0] < r1[1] and len(buckets[r1]) < bucket_size:
                            buckets[r1].append(c)
                        break #we are done
    peers = []
    for k in buckets.keys():
        peers += buckets[k]
    peers.remove(center)
    return peers


def getClosest(point, candidates):
    """Returns the candidate clostest to point."""
    return min(candidates,key=lambda x: distance(point,x))
