#! /usr/bin/python3
'''
processes are sent the PIDs of their neighbours at start
once they have them, they start telling others if they are have a degree of 1
and they listen for neighbours sending SIGUSR1 to signal they have a degree of 1(they don't know which neighbour sent it)
'''
# I want that process to be able to handle signals as soon as possible
import signal
from os import kill, mkfifo, getpid

svg_scale = 100


write_main = open('msg_main', 'w')
own_pid = str(getpid())
try:
    mkfifo('msg_'+own_pid)
except FileExistsError:
    pass
messages = open('msg_'+own_pid, 'r')

import sys
def debug(s):
    sys.stderr.write(s)
    sys.stderr.flush()

debug('test\n')
print('test')

n_of_neighbours = int(sys.argv[1])
parent_pid = int(sys.argv[2])



from time import sleep
neighbours_pid = []

write_main.write('r')#tell main we are ready
write_main.flush()

#find neighbours
position = [int(s) for s in sys.stdin.readline().split()]
debug('waiting for neighbours\n')
while len(neighbours_pid) < n_of_neighbours:
    neighbours_pid.append(int(sys.stdin.readline()))
    debug('found one neighbour\n')

debug('found all neighbours\n')

write_neighbours = [open('msg_'+str(pid), 'w') for pid in neighbours_pid]


def share_death():
    for fifo in write_neighbours:
        fifo.write('d')
        fifo.flush()
    debug('I DIED !!!\n')


#talk if needed
while True:
    if n_of_neighbours == 1:
        share_death()
    m = messages.read(1)
    # debug('received message : '+m+'\n')
    if m == 'd':
        debug("one of my neighbours died !\n")
        n_of_neighbours -= 1
        if n_of_neighbours == 0 or n_of_neighbours > 1:
            write_main.write('d')
            write_main.flush()
    elif m == 'e':
        break
    sleep(0.04)# I don't want to overload my computer if there is a bug



if n_of_neighbours > 1:
    debug("finally it has ended. Let me tell my friends I am alive\n")

    for msg in write_neighbours:
        msg.write(own_pid+' '+' '.join(str(c) for c in position)+'\n')
        msg.flush()
        msg.close()

    res = open('result.svg', 'a')
    dead_processes = 0
    while dead_processes < n_of_neighbours:
        try:
            m = messages.readline()
        except BrokenPipeError:
            break
        if m != '':
            if m == 'd\n':
                dead_processes += 1
            else:
                svg_coord = lambda x: x*svg_scale + 3*svg_scale
                dead_processes += 1
                pid = int(m.split()[0])
                if pid > int(own_pid):
                    res.write('<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:rgb(255,0,0)"/>\n'.format(svg_coord(position[0]), svg_coord(position[1]), svg_coord(float(m.split()[1])), svg_coord(float(m.split()[2]))))
                    res.flush()
    res.close()
else:
    for msg in write_neighbours:
        msg.write('d\n')
        msg.flush()
        msg.close()

    # wait till every pipe writer closed their end before dying
    dead_processes = 0
    while dead_processes < n_of_neighbours:
        try:
            m = messages.readline()
        except BrokenPipeError:
            break
        if m == '\n' or len(m.split()) == 3:
            dead_processes += 1

debug("And now I am dead.\n")
write_main.write('e')
write_main.flush()
write_main.close()

