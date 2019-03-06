#! /usr/bin/python3
from math import sqrt

# TODO : REMOVE numpy dependencies (used for matrix inversions)
from numpy import array
from numpy.linalg import inv


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
        print(k1, k2)
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

    def get_pos(self, precision=1e-10):
        """Get a rounded position at *precision* level
        """
        return (int(self.pos.x/precision)*precision,
                int(self.pos.y/precision)*precision)

    def __repr__(self):
        return 'Point('+str(self.pos.x)+', '+str(self.pos.y)+')'


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
    print(points)


    #merge points at same locations
    points_at_pos = {}
    for p in points:
        pos = p.get_pos()
        try:
            points_at_pos[pos].append(p)
        except KeyError:
            points_at_pos[pos] = [p]
    print(points_at_pos)

    points = []
    for pos in points_at_pos:
        similar_pos = points_at_pos[pos]
        points.append(similar_pos[0])
        for cousin in similar_pos[1:]:
            similar_pos[0].merge(cousin)
        for i,p2 in enumerate(similar_pos[0].linked):
            similar_pos[0].linked[i] = points_at_pos[p2.get_pos()][0]
    return points


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    points = cut([Segment(Vect(0,0), Vect(1,1)), Segment(Vect(0.1, 0.7), Vect(1, 0.2))])
    print(points)
    for p in points:
        for p2 in p.linked:
            if p2.pos.x >= p.pos.x:
                plt.plot([p.pos.x, p2.pos.x], [p.pos.y, p2.pos.y])
    plt.show()
