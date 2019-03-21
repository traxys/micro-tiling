#! /usr/bin/python3
from math import sqrt

# TODO : REMOVE numpy dependencies (used for matrix inversions)
from numpy import array
from numpy.linalg import inv
import os

class Vect:
    """Two dimensional Vector"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def norm2(self):
        """Squared norm of the vector
        """
        return self.x * self.x + self.y * self.y

    def __abs__(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, other):
        return Vect(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vect(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vect(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        return Vect(self.x / other, self.y / other)

    def __rdiv__(self, other):
        return self / other

    def __pow__(self, other):
        return self.x * other.x + self.y * other.y

    def __repr__(self):
        return "Vect("+str(self.x)+", "+str(self.y)+")"


class Segment:
    """Segment between two endpoints
    """
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __abs__(self):
        return abs(self.b - self.a)

    def intersect(self, other):
        """Calculate the intersection point beetween *self* and *other*
        """
        self_v = self.b-self.a
        other_v = other.b-other.a
        base = array([[self_v.x, other_v.x], [self_v.y, other_v.y]])
        try:
            inv_base = inv(base)
        except:
            return -1, -1
        aa = other.a - self.a
        k1 = aa.x*inv_base[0, 0] + aa.y*inv_base[0, 1]
        k2 = -aa.x*inv_base[1, 0] - aa.y*inv_base[1, 1]
        return k1, k2

    def __str__(self):
        return "segment("+str(self.a)+", "+str(self.b)+")"
    def __repr__(self):
        return str(self)


def pairs(l):
    """Iterate on pairs of segments
    """
    for i, e1 in enumerate(l):
        for e2 in l[i+1:]:
            yield e1, e2


def find_intersections(segments):
    """Find all intersections between *segments*
    """
    for s in segments:
        s.intersections = []
    for s1, s2 in pairs(segments):
        k1, k2 = s1.intersect(s2)
        if 0 <= k1 <= 1 and 0 <= k2 <= 1:
            s1.intersections.append((k1, s2))
            s2.intersections.append((k2, s1))
    for s in segments:
        s.intersections = sorted(s.intersections, key=lambda t: t[0])


class Point:
    """ Points in two dimensions
    """
    def __init__(self, pos):
        '''
        pos is a Vect
        '''
        self.pos = pos
        self.linked = []

    def merge(self, other):
        """ Tells two points are equivalent
        """
        self.linked += other.linked
        for neighbour in other.linked:
            neighbour.linked.remove(other)
            neighbour.linked.append(self)

    def get_pos(self, precision=3e-4):
        """Get a rounded position at *precision* level
        """
        return (int(self.pos.x/precision)*precision,
                int(self.pos.y/precision)*precision)

    def __repr__(self):
        return 'Point('+str(self.pos.x)+', '+str(self.pos.y)+')'


def generate_id_tuple(points):
    """Generates a tuple for each point (id, x, y, [id of linked])
    """
    largest_id = 0
    tuple_points = []
    ids = {}
    # We merge only points matching in get_pos
    for i,p in enumerate(points):
        p.id = i
    return [(p.id,
             p.pos.x,
             p.pos.y,
             [neighbour.id for neighbour in p.linked]) for p in points]


def cut(segments):
    """Cuts the *segments* such that no two segments cross
    """
    find_intersections(segments)
    points = []
    for s in segments:
        last_point = Point(s.a)
        points.append(last_point)
        for k, s2 in s.intersections:
            new_point = Point(s.a+k*(s.b-s.a))
            points.append(new_point)
            last_point.linked.append(new_point)
            new_point.linked.append(last_point)
            last_point = new_point
        new_point = Point(s.b)
        points.append(new_point)
        last_point.linked.append(new_point)
        new_point.linked.append(last_point)


    #merge points at same locations
    precision = 1./256/256# same precision as rotations
    close_positions = [(precision, 0),
                       (precision, precision),
                       (0, precision),
                       (-precision, precision),
                       (-precision, 0),
                       (-precision, -precision),
                       (0, -precision),
                       (precision, -precision)]
    points_at_pos = {}
    for p in points:
        pos = p.get_pos(precision)
        try:
            points_at_pos[pos].append(p)
        except KeyError:
            points_at_pos[pos] = [p]

    points = []
    for pos in points_at_pos:
        similar_pos = points_at_pos[pos]# list of superposed points
        points_at_pos[pos] = []
        for dx, dy in close_positions:
            try:
                similar_pos += points_at_pos[(pos[0]+dx, pos[1]+dy)]
            except KeyError:
                pass
            else:
                points_at_pos[(pos[0]+dx, pos[1]+dy)] = []
        if similar_pos:
            points.append(similar_pos[0])
            for cousin in similar_pos[1:]:
                similar_pos[0].merge(cousin)
    return points


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    points = cut([Segment(Vect(0,0), Vect(1,1)),
                  Segment(Vect(0.1, 0.7), Vect(1, 0.2)),
                  Segment(Vect(0.3, 0.75), Vect(.8, .15))])
    print([(p, len(p.linked)) for p in points])
    for p in points:
        for p2 in p.linked:
            if p2.pos.x >= p.pos.x:
                plt.plot([p.pos.x, p2.pos.x], [p.pos.y, p2.pos.y])
    plt.show()
