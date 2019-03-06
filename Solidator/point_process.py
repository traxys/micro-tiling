#! /usr/bin/python3
'''
processes are sent the PIDs of their neighbours at start
once they have them, they start telling others if they are have a degree of 1
and they listen for neighbours sending SIGUSR1 to signal they have a degree of 1(they don't know which neighbour sent it)
'''
# I want that process to be able to handle signals as soon as possible
import signal
from os import kill, mkfifo, getpid

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
    print('dead')
    debug('I DIED !!!\n')


#talk if needed
while True:
    if n_of_neighbours == 1:
        share_death()
    m = messages.read(1)
    debug('received message : '+m+'\n')
    if m == 'd':
        debug("a neighbour died !\n")
        n_of_neighbours -= 1
        if n_of_neighbours == 0 or n_of_neighbours > 1:
            write_main.write('d')
            write_main.flush()
    elif m == 'e':
        break
    sleep(0.04)#I don't want to overload my computer if there is a bug

debug("let's end this all\n")

res = open('result', 'a')
if n_of_neighbours > 1:
    res.write('hey, I am the process : '+own_pid+' and I am alive !\n')
else:
    res.write('hey, I am the process : '+own_pid+' and I am dead !\n')
res.close()
