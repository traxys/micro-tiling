#! /usr/bin/python3
'''
processes are sent the PIDs of their neighbours at start
once they have them, they start telling others if they have a degree of 1
and they listen for neighbours signaling they have a degree of 1(they don't know which neighbour sent it)
'''
# I want that process to be able to handle signals as soon as possible
import signal
from os import kill, mkfifo, getpid
import sys

svg_scale = 100

n_of_neighbours = int(sys.argv[1])
own_id = int(sys.argv[2])

write_main = open('msg_main', 'w')
own_pid = str(getpid())

messages = open('msg_'+str(own_id), 'r')

def debug(s):
    sys.stderr.write(s)
    sys.stderr.flush()

debug('test\n')
print('test')




neighbours_pid = []

write_main.write('r')#tell main we are ready
write_main.flush()

# read own coordinates on first line of input
position = [int(s) for s in sys.stdin.readline().split()]

#find neighbours
debug('waiting for neighbours\n')
while len(neighbours_pid) < n_of_neighbours:
    neighbours_pid.append(int(sys.stdin.readline()))
    # debug('found one neighbour\n')

debug('found all neighbours\n')

write_neighbours = [open('msg_'+str(point_id), 'w') for point_id in neighbours_pid]


dead_processes = 0


#talk if needed
n_of_live_neighbours = n_of_neighbours
while True:
    if n_of_live_neighbours == 1:
        # share death
        for fifo in write_neighbours:
            fifo.write('d '+str(own_id)+'\n')
            fifo.flush()
        debug('I DIED !!! '+str(own_id)+'\n')
        while True:
            m = messages.readline()
            if m[0] == 'e':
                break
            elif m[0] == 'D':
                # in case another process knows it has ended before this one does
                dead_processes += 1
        break
    m = messages.readline()
    # debug('received message : '+m+'\n')
    if m[0] == 'd':
        debug("one of my neighbours died !\n")
        n_of_live_neighbours -= 1
        if n_of_live_neighbours == 0 or n_of_live_neighbours >= 2:
            write_main.write('d')
            write_main.flush()
    elif m[0] == 'e':
        break
    elif m[0] == 'D':
        # in case another process knows it has ended before this one does
        dead_processes += 1



if n_of_live_neighbours > 1:
    debug("finally it has ended. Let me tell my friends I am alive\n")

    for msg in write_neighbours:
        msg.write('a '+str(own_id)+' '+' '.join(str(c) for c in position)+'\n')
        msg.flush()
        msg.close()

    res = open('result.svg', 'a')
    while dead_processes < n_of_neighbours:
        m = messages.readline()
        if m != '':
            if m[0] == 'D':
                dead_processes += 1
            elif m[0] == 'a':
                svg_coord = lambda x: x*svg_scale + 3*svg_scale
                dead_processes += 1
                point_id = int(m.split()[1])
                if point_id > int(own_id):
                    res.write('<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:rgb(255,0,0)"/>\n'.format(svg_coord(position[0]), svg_coord(position[1]), svg_coord(float(m.split()[2])), svg_coord(float(m.split()[3]))))
                    res.flush()
                    debug('writing line from '+str(own_id)+' to '+str(point_id)+'\n')
    res.close()
else:
    for msg in write_neighbours:
        msg.write('D\n')
        msg.flush()
        msg.close()

    # wait till every pipe writer closed their end before dying
    while dead_processes < n_of_neighbours:
        m = messages.readline()
        if m != '' and (m[0] == 'D' or m[0] == 'a'):
            dead_processes += 1

debug("And now I am dead. "+str(own_id)+"\n")
write_main.write('e')
write_main.flush()
write_main.close()

