#! /usr/bin/python3
# from matplotlib import pyplot as plt
import struct
import subprocess
import bf_interpreter


points = [(0.5, 0.7)]#, (0.6, 0.3)]
segments = [[(0.5, 0.7), (0.6, 0.3)]]

def encode(vect):
    """Takes a **point** *vect* and converts it to six bytes
    """
    s = struct.pack('>i', int(vect[0] * 256 * 256 * 256))[:-1]
    s += struct.pack('>i', int(vect[1] * 256 * 256 * 256))[:-1]
    return s


def decode(s):
    """Takes six bytes *s* and returns a **point**
    """
    x = struct.unpack('>i', s[:3]+b'\x00')[0]/256./256/256
    y = struct.unpack('>i', s[3:6]+b'\x00')[0]/256./256/256
    return (x, y)


def go_through_brainfuck(file_name, point, use_python=False):
    """ passes *points* throught the brainfuck file *file_name*
    """
    encoded = encode(point)
    if use_python:
        input_list = list(encoded)
        interpreter = bf_interpreter.Interpret(file_name,
                                               mem_size=256,
                                               get_input=lambda: chr(input_list
                                                                     .pop(0)))
        out = interpreter.get_output(6)
    else:
        p = subprocess.Popen(['bf', file_name],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        out, err = p.communicate(input=encode(point))
    return decode(out)


def mirror_and_turn(points, use_python=False):
    '''*points* need to be tuples or lists of floats
    '''
    points = list(points)
    after_symmetry = points[:]
    for point in points:
        after_symmetry.append(go_through_brainfuck('symmetry.bf',
                                                   point, use_python))

    after_rot8 = after_symmetry[:]
    for point in after_symmetry:
        after_rot8.append(go_through_brainfuck('rotate.bf', point, use_python))

    after_quarter_turn = after_rot8[:]
    being_turned = after_quarter_turn[:]
    for _ in range(3):
        for i, point in enumerate(being_turned):
            being_turned[i] = go_through_brainfuck('quarter_turn.bf',
                                                   point,
                                                   use_python)
            after_quarter_turn.append(being_turned[i])

    return after_quarter_turn


def mirror_and_turn_segments(segments, use_python=False):
    '''
        *segments* need to be tuples or lists of **points**
        (will be returned as tuples),
        **points** need to be tuples or lists of floats
    '''
    return zip(mirror_and_turn((s[0] for s in segments), use_python),
               mirror_and_turn((s[1] for s in segments), use_python))


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    # points :
    '''
    result = mirror_and_turn(points)
    plt.plot([p[0] for p in result], [p[1] for p in result])
    '''
    
    # segments :
    result = mirror_and_turn_segments(segments)
    for s in result:
        plt.plot([s[i][0] for i in [0,1]], [s[i][1] for i in [0,1]])

    plt.show()
