import pymultihash as MultiHash

import random

def idToPoint(dim,id):
    """
    We're using a unit space for the position of our nodes.
    The mapping we use is to use the hash ID as the seed to an RNG.
    We should switch to either
    1) A universal RNG
    2) The mapping done by Symphony
    """
    idLong = MultiHash.parseHash(id)
    random.seed(idLong)
    return tuple([random.random() for x in range(dim)])

def distance(p0,p1):
    """Returns the distance from point 1 to point 2?"""
    return sum([(a-b)**2.0 for a,b in zip(p0,p1)])**0.5

def midpoint(p0,p1):
    """Returns the midpoint between two points in a Euclidean Space"""
    return tuple([(a+b)/2.0 for a,b in zip(p0,p1)])

def getDelaunayPeers(candidates,center):
    """
    This is the Distrubuted Greedy Voronoi Heuristic.

    center is some point in a space (we don't really care which) and the 
    heuristic decides which of the candidates are members of Delaunay 
    Triangulations with the center point.

    This allows a node located at center to quickly figure out its 
    Voronoi region.

    Error rate: Our heuristic overestimates approximately edge per node

    """
    if len(candidates) < 2:
        return candidates
    sortedCandidates = sorted(candidates,key=lambda x: distance(x,center))
    peers = [sortedCandidates[0]] #create a new list, initialized closest peer
    sortedCandidates = sortedCandidates[1:]
    for c in sortedCandidates:
        m = midpoint(c,center)
        accept = True
        for p in peers:
            if distance(m,p) < distance(m,center):  # if occluded by previous peer
                accept = False
                break
        if accept:
            peers.append(c)
    return peers

def getClosest(point,candidates):
    """Returns the candidate clostest to point."""
    return min(candidates,key=lambda x: distance(point,x))


