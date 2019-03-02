#! /usr/bin/python3
from matplotlib import pyplot as plt
import struct
import subprocess

points = [(0.5, 0.7)]#, (0.2, 0.3)]


def encode(vect):
    s = struct.pack('>i', int(vect[0]*256*256*256))[:-1]
    s+= struct.pack('>i', int(vect[1]*256*256*256))[:-1]
    return s

def decode(s):
    x = struct.unpack('>i', s[:3]+b'\x00')[0]/256./256/256
    y = struct.unpack('>i', s[3:6]+b'\x00')[0]/256./256/256
    return (x,y)


def go_through_brainfuck(file_name, point):
    encoded = encode(point)
    p = subprocess.Popen(['bf', file_name], stdout = subprocess.PIPE, stdin = subprocess.PIPE)
    out, err = p.communicate(input=encode(point))
    return decode(out)


def mirror_and_turn(points):
    '''
    points need to be tuples or lists of floats
    '''
    after_symmetry = list(points)[:]
    for point in points:
        after_symmetry.append(go_through_brainfuck('symmetry.bf', point))

    after_rot8 = after_symmetry[:]
    for point in after_symmetry:
        after_rot8.append(go_through_brainfuck('rotate.bf', point))

    after_quarter_turn = after_rot8[:]
    being_turned = after_quarter_turn[:]
    for _ in range(3):
        for i, point in enumerate(being_turned):
            being_turned[i] = go_through_brainfuck('quarter_turn.bf', point)
            after_quarter_turn.append(being_turned[i])

    return after_quarter_turn

def mirror_and_turn_segments(segments):
    '''
    segments need to be tuples or lists of points (will be returned as tuples)
        points need to be tuples or lists of floats
    '''
    return zip(mirror_and_turn(s[0] for s in segments), mirror_and_turn(s[1] for s in segments))


if __name__ == "__main__":
    result = mirror_and_turn(points)
    print(result)
    plt.plot([p[0] for p in result], [p[1] for p in result])
    plt.show()
