#! /usr/bin/python3
from math import sqrt

class Vect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
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
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __abs__(self):
        return abs(self.b - self.a)

class Point:
    def __init__(self, pos):
        '''
        pos is a Vect
        '''
        self.pos = pos
        self.linked = []
    def merge(self, other):
        self.linked += other.linked
    def get_pos(self, precision = 1e-10):
        return (int(self.pos.x/precision)*precision,  int(self.pos.y/precision)*precision)

    def __repr__(self):
        return 'Point('+str(self.pos.x)+', '+str(self.pos.y)+')'


def remove_deg_1(points):

    deg1 = [p for p in points if len(p.linked)==1]

    while deg1:
        p = deg1.pop()
        p.linked[0].linked.remove(p)
        if len(p.linked[0].linked) == 1:
            deg1.append(p.linked[0])

    return [p for p in points if len(p.linked)>1]


if __name__ == "__main__":
    print(remove_deg_1([Point(Vect(1,1))]))

