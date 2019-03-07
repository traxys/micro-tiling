#! /usr/bin/python3
import struct
import subprocess
import bf_interpreter


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


def decode_nine(s):
    """Decode nine **points** from *s*
    """
    return [decode(s[6*i:6*(i+1)]) for i in range(9)]


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
    return decode_nine(out)


def translate_segments(segments, use_python=False):
    """Translate and copies each *segments* in all eight direction
    """
    out = []
    for s in segments:
        pointsa = go_through_brainfuck('translator.bf', s[0], use_python)
        pointsb = go_through_brainfuck('translator.bf', s[1], use_python)
        out += list(zip(pointsa, pointsb))
    return out


if __name__ == "__main__":
    print(translate_segments([[[1,1],[0,0]]]))
