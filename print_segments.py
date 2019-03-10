#!/bin/python3

import json
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def load(file):
    f = open(file, "r")
    segments = json.loads(f.read())
    f.close()
    return segments


def display(segments):
    line_segments = LineCollection(segments)
    ax = plt.axes()
    ax.add_collection(line_segments)
    plt.show()


if __name__ == "__main__":
    import sys
    display(load(sys.argv[1]))
