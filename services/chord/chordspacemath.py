
"""
PLEASE READ THE FOLLOWING ASSUMPTIONS


Chord exists in a 1-d ring
All functions that do any useful math use the location of the node in this ring
the location is a base 10 int, not the actual hash



"""


import pymultihash as multihash





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
    if left ==  right:
        return True
    if target == left or target == right:
        return False
    #print target, "<", right, "and", target, ">", left, target < right and target > left
    if target < right and target > left:
        return True
    #print left, ">", right, left > right 
    if left > right :
        #print left, ">", target, "and", target, "<", right, left > target and target < right
        if left > target and target < right:
            return True
        #print left, "<", target, "and", target, ">", right, left < target and target > right
        if left < target and target > right:
            return True
    return False




def isPointBetweenRightInclusive(target, left, right):
    if target == right:
        return True
    return isPointBetween(target, left, right)

#TODO don't assume max is 160
MAX = 2**160



def distance(origin, destination):
    """
    measures the distance it takes to get to the destination
    traveling from origin 
    """
    assert(isinstance(origin, int))
    dist =  destination - origin
    if dist < 0:
        return MAX + dist
    return dist

def getClosest(point,candidates):
    """Returns the candidate closest to point without going over."""
    return min(candidates, key=lambda x: distance(x, point))

def getBestSuccessor(point, candidates):
    return min(candidates, key=lambda x: distance(point, x))

if __name__ == '__main__':
    testCandidates =  [int(2**159 - 7000),  100,400,499, 600]
    print(getClosest(20, testCandidates))
    print(getBestSuccessor(500, testCandidates))
    print(list(map(lambda x: distance(x,500), testCandidates)))