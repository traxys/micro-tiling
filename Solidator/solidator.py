#! /usr/bin/python3
from math import sqrt
import subprocess, signal
from os.path import abspath
from os import getpid, mkfifo
from time import sleep
import sys

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


def open_process(point):
    proc = subprocess.Popen([abspath('./point_process.py'), str(len(point.linked)), str(getpid())], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = sys.stdout)
    return proc

def remove_deg_1(points, multithread = True):
    if multithread:
        mkfifo('msg_main')
        number_deg1 = 0
        for p in points:
            if len(p.linked) == 1:
                number_deg1 += 1
            p.proc = open_process(p)
        messages = open('msg_main', 'r')

        for p in points:
            try:
                mkfifo('msg_'+str(p.proc.pid))
            except FileExistsError:
                pass
            p.msg = open('msg_'+str(p.proc.pid), 'w')

        unprepared_processes = len(points)
        while unprepared_processes:
            print('waiting for '+str(unprepared_processes)+' processes')
            messages.read(1)
            unprepared_processes -= 1

        for p in points:
            for neighbour in p.linked:
                p.proc.stdin.write(bytes(str(neighbour.proc.pid), 'utf-8')+b'\n')
                p.proc.stdin.flush()
                print('wrote one neighbour')
        

        while number_deg1:
            print('deg1 left :',number_deg1)
            messages.read(1)
            number_deg1 -= 1
            sleep(0.1)
    
        res = open('result', 'w')
        res.close()
        for p in points:
            p.msg.write('e')#tell them it is the end
            p.msg.flush()
            p.msg.close()
        return []

    else:
        deg1 = [p for p in points if len(p.linked)==1]

        while deg1:
            p = deg1.pop()
            p.linked[0].linked.remove(p)
            if len(p.linked[0].linked) == 1:
                deg1.append(p.linked[0])
            p.linked = []

        return [p for p in points if len(p.linked)>1]


if __name__ == "__main__":
    def link(p1, p2):
        p1.linked.append(p2)
        p2.linked.append(p1)

    p1 = Point(Vect(1,1))
    p2 = Point(Vect(0,0))
    p3 = Point(Vect(1,-1))
    p4 = Point(Vect(1,0))
    
    link(p1,p2)
    link(p2,p3)
    link(p3,p4)
    link(p2,p4)
    
    
    print(remove_deg_1([p1, p2, p3, p4]))

