import vendored.pymultihash as MultiHash

import random

def id_to_point(dim,id):
    id_long = MultiHash.parseHash(id)
    random.seed(id_long)
    return tuple([random.random() for x in range(dim)])

def distance(p0,p1):
    return sum([(a-b)**2.0 for a,b in zip(p0,p1)])**0.5

def midpoint(p0,p1):
    return tuple([(a+b)/2.0 for a,b in zip(p0,p1)])

def getDelaunayPeers(canidates,center):
    """
    This is DGVH. We should replace it with exact 2d delaunay
    """
    if len(canidates) < 2:
        return canidates
    sorted_canidates = sorted(canidates,key=lambda x: distance(x,center))
    peers = [sorted_canidates[0]]
    sorted_canidates = sorted_canidates[1:]
    for c in sorted_canidates:
        m = midpoint(c,center)
        accept = True
        for p in peers:
            if distance(m,p) < distance(m,center):
                accept = False
                break
        if accept:
            peers.append(c)
    return peers

def getClosest(point,canidates):
    return min(canidates,key=lambda x: distance(point,x))


