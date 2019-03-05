#! /usr/bin/python3
"""Module clipping lines in the unit square
"""


class p:
    """Class defining a two dimensional point in space"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return p(self.x+other.x, self.y+other.y)

    def __sub__(self, other):
        return p(self.x-other.x, self.y-other.y)

    def __mul__(self, other):
        return p(self.x*other, self.y*other)

    def __str__(self):
        return '('+str(self.x)+', '+str(self.y)+')'


class segment:
    """Class representing a segment by the two endpoints
    """
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return '('+str(self.a)+', '+str(self.b)+')'

    def __repr__(self):
        return str(self)


lines = [segment(p(0, 0.4), p(1.5, 1.5))]


def clip_right(lines):
    """Clip *lines* with a vertical line to the right
    """
    out = []
    for l in lines:
        if l.a.x == l.b.x:
            if l.a.x < 1:
                out.append(l)
        else:
            k = (l.a.x-1)/(l.a.x-l.b.x)
            ab = p(l.b.x-l.a.x, l.b.y-l.a.y)
            if 0 < k < 1:
                if l.a.x > l.b.x:
                    out.append(segment(l.a + ab*k, l.b))
                else:
                    out.append(segment(l.a, l.b - ab*(1-k)))
            else:
                out.append(l)
    return out


def turn_right(lines):
    """Rotates *lines* by 90 degrees
    """
    for l in lines:
        l.a.x, l.a.y = l.a.y, -l.a.x
        l.b.x, l.b.y = l.b.y, -l.b.x


def clip_unit_square(lines):
    """Clip *lines* to fit in the unit square
    """
    for _ in range(4):
        turn_right(lines)
        lines = clip_right(lines)
    return lines

