#! /usr/bin/python3
from matplotlib import pyplot as plt
from math import sin, cos, sqrt
import struct

import subprocess

n = 400
pi2 = 3.14159265358979323846264*2
r2 = 2**.5/2
points = [(sin(t*pi2/n), cos(t*pi2/n)) for t in range(n+1)]


def encode(vect):
    s = struct.pack('>i', int(vect[0]*256*256))[1:]
    s+= struct.pack('>i', int(vect[1]*256*256))[1:]
    return s

def decode(s):
    x = struct.unpack('>i', s[:3]+b'\x00')[0]/256./256/256
    y = struct.unpack('>i', s[3:6]+b'\x00')[0]/256./256/256
    return (x,y)




after_rot = []
for vect in points:
    p = subprocess.Popen(['bf', 'rotate.bf'], stdout = subprocess.PIPE, stdin = subprocess.PIPE)
    out, err = p.communicate(input=encode(vect))
    if len(out) > 6:
        print([encode(vect)])
    after_rot.append(decode(out))


def distance(p1, p2):
    return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def py_rotate(p):
    return (p[0]*r2-p[1]*r2, p[0]*r2+p[1]*r2)


px = [p[0] for p in points]
py = [p[1] for p in points]
plt.plot(px, py)
px = [p[0] for p in after_rot]
py = [p[1] for p in after_rot]
plt.plot(px, py)
plt.show()
