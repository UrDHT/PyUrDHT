import pymultihash as MultiHash

import random

import math

def idToPoint(dim,id):
    assert(dim == 2)
    """
    We're using a unit space for the position of our nodes.
    The mapping we use is to use the hash ID as the seed to an RNG.
    We should switch to either
    1) A universal RNG
    2) The mapping done by Symphony
    """
    idLong = MultiHash.parseHash(id)
    random.seed(idLong)
    r = random.random()**0.5
    theta = random.random()*math.pi*2
    x = math.cos(theta)*r
    y = math.sin(theta)*r
    return (x, y)

def fEq(a, b):
    return abs(a - b) <= 0.000001


def dot(a, b):
    return sum(map(lambda x, y: x * y, a, b))


def cross(a):
    # assumes 2d
    return (-1 * a[1], a[0])


def klein2poincare(s):
    assert(dot(s, s) < 1)
    return tuple(map(lambda x: x / (1 + (1 - dot(s, s))**0.5), s))


def poincare2klein(u):
    assert(dot(u, u) < 1)
    return tuple(map(lambda x: (x * 2) / (1 + dot(u, u)), u))


def eMid(a, b):
    return tuple(map(lambda x, y: (x + y) / 2, a, b))


def eDist(a, b):
    return sum(map(lambda x, y: (x - y)**2.0, a, b))**0.5


def hDist(a, b):

    sigma = 2 * eDist(a, b)**2.0 / ((1 - dot(a, a)) * (1 - dot(b, b)))
    return math.acosh(1 + sigma)


def normalize(vec):

    mag = dot(vec, vec)**0.5
    return tuple(map(lambda x: x / mag, vec))


def point2lineDist(p0, p1, p2):
    # p1 and p2 form a line
    return math.fabs((p2[1] - p1[1]) * p0[0] -
                     (p2[0] - p1[0]) * p0[1] + p2[0] * p1[1] - p2[1] * p1[0]) /\
        eDist(p1, p2)


def kleinIdealPts(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dr = (dx * dx + dy * dy)**0.5
    D = a[0] * b[1] - b[0] * a[1]
    x_0 = (D * dy + dx * (dr * dr - D * D)**0.5) / (dr * dr)
    x_1 = (D * dy - dx * (dr * dr - D * D)**0.5) / (dr * dr)
    y_0 = (-1 * D * dx + dy * (dr * dr - D * D)**0.5) / (dr * dr)
    y_1 = (-1 * D * dx - dy * (dr * dr - D * D)**0.5) / (dr * dr)

    secant_candiates = list(
        set([(x_0, y_0), (x_1, y_0), (x_0, y_1), (x_1, y_1)]))
    output = []
    for s in secant_candiates:
        if fEq(point2lineDist(s, a, b), 0) and fEq(dot(s, s), 1.0):
            output.append(s)
            if(len(output) == 2):
                break
    assert(len(output) == 2)
    return output


def lineIntersect(p1, p2, p3, p4):
    pole_x = 0
    pole_y = 0
    try:
        pole_x = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[0] - p4[0]) - (p1[0] - p2[0]) * (p3[0] * p4[1] - p3[1] * p4[0])) / (
            (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0]))
    except:
        print("parallel")
        pole_x = float("inf")
        return (pole_x, poley)
    try:
        pole_y = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] * p4[1] - p3[1] * p4[0])) / (
            (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0]))
    except:
        print("parallel")
        pole_y = float("inf")
        return (pole_x, poley)

    pole = (pole_x, pole_y)

    assert(fEq(point2lineDist(pole, p1, p2), 0))
    assert(fEq(point2lineDist(pole, p3, p4), 0))

    return pole


def kleinPole(a, b):
    p1, p3 = kleinIdealPts(a, b)
    p2 = map(lambda x, y: x + y, p1, cross(p1))
    p4 = map(lambda x, y: x + y, p3, cross(p3))
    pole = lineIntersect(p1, p2, p3, p4)
    assert(fEq(eDist(p1, pole), eDist(p3, pole)))
    return pole


def hMid(a, b):
    k_a = poincare2klein(a)
    k_b = poincare2klein(b)
    assert(dot(k_a, k_a) < 1.0)

    assert(dot(k_b, k_b) < 1.0)
    pole = kleinPole(k_a, k_b)
    a_pts = sorted(kleinIdealPts(pole, k_a), key=lambda x: eDist(x, pole))
    b_pts = sorted(kleinIdealPts(pole, k_b), key=lambda x: eDist(x, pole))
    mid = (0, 0.99999)
    for p0 in a_pts:
        for p1 in b_pts:
                test_mid = lineIntersect(a_pts[0], b_pts[1], k_a, k_b)
                if dot(test_mid, test_mid) < 1.0 and fEq(hDist(k_a, test_mid), hDist(k_b, test_mid)):
                    mid = test_mid
    # if not fEq(hDist(k_a, mid), hDist(k_b, mid)):
    #    print(hDist(k_a, mid), hDist(k_b, mid))
    # assert(fEq(hDist(k_a, mid), hDist(k_b, mid)))
    return klein2poincare(mid)



def distance(p0, p1):
    """Returns the distance from point 1 to point 2?"""
    return hDist(p0, p1)

def midpoint(p0, p1):
    """Returns the midpoint between two points in a Euclidean Space"""
    return eMid(p0, p1)

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
