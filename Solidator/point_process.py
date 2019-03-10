#! /usr/bin/python3
'''
processes are sent the IDs of their neighbours at start
once they have them, they start telling others if they have a degree of 1
and they listen for neighbours signaling they have a degree of 1
'''
import sys

svg_scale = 100
line_blueprint = '<line x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:rgb(255,0,0)"/>\n'

n_of_neighbours = int(sys.argv[1])
own_id = int(sys.argv[2])

write_main = open('msg_main', 'w')

messages = open('msg_'+str(own_id), 'r')

def debug(string):
    '''write in stderr and add the point id for clarity
    '''
    sys.stderr.write('('+str(own_id)+') '+string)
    sys.stderr.flush()

debug('process starting\n')




neighbours_pid = []

write_main.write('r')#tell main we are ready
write_main.flush()

# read own coordinates on first line of input
position = [int(coord) for coord in sys.stdin.readline().split()]

#find neighbours
debug('waiting for neighbours\n')
while len(neighbours_pid) < n_of_neighbours:
    neighbours_pid.append(int(sys.stdin.readline()))

debug('found all neighbours\n')

write_neighbours = [open('msg_'+str(point_id), 'w') for point_id in neighbours_pid]


dead_processes = 0

n_of_live_neighbours = n_of_neighbours

# states
dead = False
end = False

while not(end) or dead_processes < n_of_neighbours:
    if not(dead) and n_of_live_neighbours == 1:
        # share death
        for fifo in write_neighbours:
            fifo.write('d '+str(own_id)+'\n')
            fifo.flush()
        debug('I DIED !!!\n')
        dead = True

    m = messages.readline()

    if m[0] == 'e':
        end = True
        res = open('result.svg', 'a')
        if dead:
            for msg in write_neighbours:
                msg.write('D\n')
                msg.flush()
                msg.close()
        else:
            for msg in write_neighbours:
                msg.write('a '+str(own_id)+' '+' '.join(str(c) for c in position)+'\n')
                msg.flush()
                msg.close()
    elif m[0] == 'D':
        dead_processes += 1
    elif m[0] == 'd':
        if not dead:
            debug("one of my neighbours died !\n")
            n_of_live_neighbours -= 1
            if n_of_live_neighbours == 0 or n_of_live_neighbours >= 2:
                write_main.write('d')
                write_main.flush()
    elif m[0] == 'a':
        dead_processes += 1
        if not dead:
            svg_coord = lambda x: x*svg_scale + 3*svg_scale
            point_id = int(m.split()[1])
            if point_id > int(own_id):
                res.write(line_blueprint.format(svg_coord(position[0]),
                                                svg_coord(position[1]),
                                                svg_coord(float(m.split()[2])),
                                                svg_coord(float(m.split()[3]))))
                res.flush()
                debug('writing line from '+str(own_id)+' to '+str(point_id)+'\n')


res.close()

debug("And now I am dead.\n")
write_main.write('e')
write_main.flush()
write_main.close()
