#! /usr/bin/python3
from math import sqrt
import subprocess
from os.path import abspath
from os import getpid, mkfifo, system
from time import sleep
import sys


class Vect:
    """A two dimensional vector
    """
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
    """A segment of two vectors
    """
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __abs__(self):
        return abs(self.b - self.a)


class Point:
    """ A two dimensional point whose *pos* is a **Vect**
    """
    def __init__(self, pos):
        '''
        pos is a Vect
        '''
        self.pos = pos
        self.linked = []

    def merge(self, other):
        """Merges with another **Point**
        """
        self.linked += other.linked

    def get_pos(self, precision=1e-10):
        """Returns an position up to *precision*
        """
        return (int(self.pos.x/precision)*precision,
                int(self.pos.y/precision)*precision)

    def __repr__(self):
        return 'Point('+str(self.pos.x)+', '+str(self.pos.y)+')'


def open_process(point):
    '''opens a process representing a *point*
    tells it how many neighbours it should expect and its *point* *id*
    '''
    proc = subprocess.Popen([abspath('./point_process.py'),
                             str(len(point.linked)),
                             str(point.id)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=sys.stdout)
    return proc


def remove_deg_1(points, multiprocess=True):
    '''write an svg with only closed polygons displayed
    '''
    if multiprocess:
        # cleanup what might have been left from before
        system('rm msg_*')
        mkfifo('msg_main')
        number_deg1 = 0

        # create named pipes necessary for communication
        for i, p in enumerate(points):
            p.id = i
            mkfifo('msg_' + str(p.id))

        # open one process for each point
        # (and count the number of points of degree 1)
        for p in points:
            if len(p.linked) == 1:
                number_deg1 += 1
            p.proc = open_process(p)
        messages = open('msg_main', 'r')

        # open communication pipes for each process
        for p in points:
            p.msg = open('msg_' + str(p.id), 'w')

        # wait untill every process has finished starting up
        unprepared_processes = len(points)
        while unprepared_processes:
            print('waiting for ' + str(unprepared_processes) + ' processes')
            m = messages.read(1)
            if m == 'r':
                unprepared_processes -= 1

        # tell each process the position of the point they represent
        # and the id of their neighbours
        for p in points:
            p.proc.stdin.write(bytes(str(p.pos.x) +
                                     ' ' +
                                     str(p.pos.y),
                                     'utf-8') + b'\n')
            for neighbour in p.linked:
                p.proc.stdin.write(bytes(str(neighbour.id), 'utf-8') + b'\n')
                p.proc.stdin.flush()

        # wait for all points of degree 1 to be deleted
        # (associated processes are still running,
        # they just know they shouldn't be displayed on the result)
        while number_deg1:
            print('deg1 left :', number_deg1)
            m = messages.read(1)
            if m == 'd':
                number_deg1 -= 1
            sleep(0.1)
    
        # write svg header
        res = open('result.svg', 'w')
        res.write('<svg width="600" height="600">\n')
        res.flush()
        res.close()
        for p in points:
            # tell processes they can write the result and die
            p.msg.write('e\n')
            p.msg.flush()
            p.msg.close()

        # wait for all processes to die
        processes_alive = len(points)
        while processes_alive > 0:
            print(processes_alive, 'processes still alive')
            m = messages.read(1)
            print('message :',m)
            if m == 'e':
                processes_alive -= 1
            sleep(0.1)
        print('all processes dead')

        # write svg footer
        res = open('result.svg', 'a')
        res.write('</svg>\n')
        res.flush()
        res.close()

    else:
        deg1 = [p for p in points if len(p.linked)==1]

        while deg1:
            p = deg1.pop()
            p.linked[0].linked.remove(p)
            if len(p.linked[0].linked) == 1:
                deg1.append(p.linked[0])
            p.linked = []


        # write result in svg
        res = open('result.svg', 'w')
        res.write('<svg width="600" height="600">\n')

        line_blueprint = '<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:rgb(255,0,0)"/>\n'
        svg_scale = 100
        svg_coord = lambda x: x*svg_scale + 3*svg_scale
        for p in points:
            for p2 in p.linked:
                res.write(line_blueprint.format(svg_coord(position[0]),
                                                svg_coord(position[1]),
                                                svg_coord(float(m.split()[2])),
                                                svg_coord(float(m.split()[3]))))
        res.write('</svg>\n')
        res.flush()
        res.close()


if __name__ == "__main__":
    def link(p1, p2):
        p1.linked.append(p2)
        p2.linked.append(p1)

    p1 = Point(Vect(1, 1))
    p2 = Point(Vect(0, 0))
    p3 = Point(Vect(1, -1))
    p4 = Point(Vect(1, 0))
    p5 = Point(Vect(1, 2))
    p6 = Point(Vect(2, 1))
    
    link(p5, p1)
    link(p6, p1)
    link(p1, p2)
    link(p2, p3)
    link(p3, p4)
    link(p2, p4)
    
    points = [p1, p2, p3, p4, p5, p6]
    img = open('initial_img.svg','w')
    img.write('<svg width="600" height="600">\n')
    svg_scale = 100
    svg_coord = lambda x: x*svg_scale + 3*svg_scale
    for p in points:
        for p2 in p.linked:
            img.write('<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:rgb(255,0,0)"/>\n'.format(svg_coord(p.pos.x), svg_coord(p.pos.y), svg_coord(p2.pos.x), svg_coord(p2.pos.y)))

    img.write('</svg>\n')
    img.flush()
    img.close()
    remove_deg_1(points)

