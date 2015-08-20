import pymultihash as multihash


""" Converts a hashkey into some point"""
def id2Point(id):
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


#TODO distance sucks
def distance(a, b):
    assert(isinstance(a, int))
    dist =  b - a
    if dist <= 0:
        return MAX + dist
    return dist

def getClosest(point,candidates):
    """Returns the candidate clostest to point."""
    return min(candidates,key=lambda x: distance(point,x))