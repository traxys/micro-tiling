#! /usr/bin/python3
'''
processes are sent the IDs of their neighbours at start
once they have them, they start telling others if they have a degree of 1
and they listen for neighbours signaling they have a degree of 1


signification of messages to point_processes :
    e : message comming from main meaning it is now time to write
        the result.

    d <neighbour_id> : the neighbouring point with neighbour_id
        had only one neighbour left 'alive' and is therefore
        now 'dead'.
    
    a : death acknowledge means the neighbour now knows the point is 'dead'

    A <neighbour_id> <neighbour_x_pos> <neighbour_y_pos> : the
        corresponding neighbour is still 'alive' (sent after the neighbour
        received a message 'e').

    D : a neighbour is 'dead' and no line should be displayed between the
        two points.
'''
import sys

svg_scale = 100
line_blueprint = '<line x1="{}" y1="{}" x2="{}" y2="{}"\
                  style="stroke:rgb(255,0,0)"/>\n'


def debug(string, own_id):
    '''write a *string*  in stderr and add the point's *own_id* for clarity
    '''
    sys.stderr.write('(' +
                     str(own_id) +
                     ') ' +
                     string)
    sys.stderr.flush()


def read_position():
    """Reads a line from **stdin** and interprets it as a position
    """
    return [float(coord) for coord in sys.stdin.readline().split()]


def read_neighbours(amount):
    """Reads *amount* neighbours from **stdin**
    """
    neighbours_pid = []
    while len(neighbours_pid) < amount:
        neighbours_pid.append(int(sys.stdin.readline()))
    return neighbours_pid


def signal_death(neighbour_messagers, own_id):
    """Tells all neighbours of *own_id* death by *neighbour_messagers*' fifo files
    """
    for fifo in neighbour_messagers:
        fifo.write('d '+str(own_id)+'\n')
        fifo.flush()
    debug('I DIED !!!\n', own_id)

def death_ack(fifo):
    fifo.write('a\n')
    fifo.flush()

def who_am_i_at_the_end(is_dead, neighbour_messagers, own_id, position):
    """Tells all neighbours by *neighbour_messagers*
    the vertex *own_id* and *position* if not *is_dead*,
    else send them D
    """
    if is_dead:
        for msg in neighbour_messagers:
            msg.write('D\n')
            msg.flush()
            msg.close()
    else:
        for msg in neighbour_messagers:
            msg.write('A ' +
                      str(own_id) +
                      ' ' +
                      ' '.join(str(c) for c in position) +
                      '\n')
            msg.flush()
            msg.close()


def svg_coord(x):
    """Returns the coordinate in svg space for *x*
    """
    return x * svg_scale + 3 * svg_scale


def svg_output(message, own_id, position, res):
    """Outputs to *res* the svg line from *position* to the neighbour
    indicated in *message* if *own_id* is smaller than
    the neighbour's id (this is to avoid writing twice the same line)
    """
    point_id = int(message.split()[1])
    if point_id > int(own_id):
        res.write(line_blueprint.format(svg_coord(position[0]),
                                        svg_coord(position[1]),
                                        svg_coord(float(message.split()[2])),
                                        svg_coord(float(message.split()[3]))))
        res.flush()


def main():
    """Waits for processes to die around you to check if you can survive
    """
    n_of_neighbours = int(sys.argv[1])
    own_id = int(sys.argv[2])

    # open ressources
    write_main = open('msg_main', 'w')
    messages = open('msg_' + str(own_id), 'r')

    debug('process starting\n', own_id)

    neighbours_pid = []

    write_main.write('r')  # tell main we are ready
    write_main.flush()

    # read own coordinates on first line of input
    position = read_position()

    # find neighbours
    neighbours_id = read_neighbours(n_of_neighbours)
    write_neighbours = [open('msg_' + str(point_id), 'w')
                        for point_id in neighbours_id]

    dead_processes = 0
    n_of_live_neighbours = n_of_neighbours

    # states
    dead = False
    end = False
    neighbour_knows_im_dead = False

    while not(end) or dead_processes < n_of_neighbours:
        if not(dead) and n_of_live_neighbours == 1:
            signal_death(write_neighbours, own_id)
            dead = True

        m = messages.readline()

        if m == '':
            continue
        elif m[0] == 'e':
            end = True
            res = open('result.svg', 'a')
            who_am_i_at_the_end(dead, write_neighbours, own_id, position)

        elif m[0] == 'd':
            debug("one of my neighbours died !\n", own_id)
            
            dead_id = int(m.split()[1])
            if not neighbour_knows_im_dead:
                death_ack(write_neighbours[neighbours_id.index(dead_id)])
                debug("and he died before me !\n", own_id)
                n_of_live_neighbours -= 1
                if n_of_live_neighbours == 0 or n_of_live_neighbours >= 2:
                    write_main.write('d')
                    write_main.flush()

        elif m[0] == 'a':
            neighbour_knows_im_dead = True

        elif m[0] == 'D':
            dead_processes += 1

        elif m[0] == 'A':
            dead_processes += 1
            if not dead:
                svg_output(m, own_id, position, res)

    res.close()

    debug("And now I am dead.\n", own_id)
    write_main.write('e')
    write_main.flush()
    write_main.close()


if __name__ == "__main__":
    main()
