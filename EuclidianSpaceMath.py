import pymultihash as MultiHash

import random

def idToPoint(dim,id):
    idLong = MultiHash.parseHash(id)
    random.seed(idLong)
    return tuple([random.random() for x in range(dim)])

def distance(p0,p1):
    return sum([(a-b)**2.0 for a,b in zip(p0,p1)])**0.5

def midpoint(p0,p1):
    return tuple([(a+b)/2.0 for a,b in zip(p0,p1)])

def getDelaunayPeers(candidates,center):
    """
    This is DGVH. We should replace it with exact 2d delaunay
    """
    if len(candidates) < 2:
        return candidates
    sortedCandidates = sorted(candidates,key=lambda x: distance(x,center))
    peers = [sortedCandidates[0]]
    sortedCandidates = sortedCandidates[1:]
    for c in sortedCandidates:
        m = midpoint(c,center)
        accept = True
        for p in peers:
            if distance(m,p) < distance(m,center):
                accept = False
                break
        if accept:
            peers.append(c)
    return peers

def getClosest(point,candidates):
    return min(candidates,key=lambda x: distance(point,x))


