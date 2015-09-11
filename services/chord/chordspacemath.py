
"""
PLEASE READ THE FOLLOWING ASSUMPTIONS


Chord exists in a 1-d ring
All functions that do any useful math use the location of the node in this ring
the location is a base 10 int, not the actual hash
"""


import pymultihash as multihash


# TODO don't assume max is 160
KEYSIZE = 256
MAX = 2 ** KEYSIZE


def idToPoint(id):
    """
    Converts a hashkey into some point

    Keyword Arguments:
    id -- the multihash id/key of a node/value
    """
    idLong = multihash.parseHash(id)
    return idLong


def isPointBetween(target, left, right):
    assert isinstance(target, int)
    if left == right:
        return True
    if target == left or target == right:
        return False
    if target < right and target > left:
        return True
    if left > right:
        if left > target and target < right:
            return True
        if left < target and target > right:
            return True
    return False


def isPointBetweenRightInclusive(target, left, right):
    if target == right:
        return True
    return isPointBetween(target, left, right)


def distance(origin, destination):
    """
    measures the distance it takes to get to the destination
    traveling from origin
    """
    assert(isinstance(origin, int))
    dist = destination - origin
    if dist < 0:
        return MAX + dist
    return dist


def getClosest(point, candidates):
    """Returns the candidate closest to point without going over."""
    return min(candidates, key=lambda x: distance(x.loc, point))


def getBestSuccessor(point, candidates):
    return min(candidates, key=lambda x: distance(point, x.loc))
