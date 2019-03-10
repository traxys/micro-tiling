#! /usr/bin/python3
'''
processes are sent the IDs of their neighbours at start
once they have them, they start telling others if they have a degree of 1
and they listen for neighbours signaling they have a degree of 1
'''
import sys

svg_scale = 100
line_blueprint = '<line x1="{}" y1="{}" x2="{}" y2="{}"\
                  style="stroke:rgb(255,0,0)"/>\n'


def debug(string, own_id):
    '''write a *string*  in stderr and add the point *own_id* for clarity
    '''
    sys.stderr.write('(' +
                     str(own_id) +
                     ') ' +
                     string)
    sys.stderr.flush()


def read_position():
    """Reads a line from **stdin** and interprets it as a position
    """
    return [int(coord) for coord in sys.stdin.readline().split()]


def read_neighbours(amount):
    """Reads *amount* neighbours from **stdin**
    """
    neighbours_pid = []
    while len(neighbours_pid) < amount:
        neighbours_pid.append(int(sys.stdin.readline()))
    debug('found all neighbours\n')
    return neighbours_pid


def signal_death(neighbour_messager, own_id):
    """Tells all neighbours of *own_id* death by *neighbour_messager*
    """
    # share death
    for fifo in neighbour_messager:
        fifo.write('d '+str(own_id)+'\n')
        fifo.flush()
    debug('I DIED !!!\n')


def who_am_i_at_the_end(is_dead, neighbour_messenger, own_id, position):
    """Tells all neighbours by *neighbour_messenger*
    the vertex *own_id* and *position* if not *is_dead*,
    else send them D
    """
    if is_dead:
        for msg in neighbour_messenger:
            msg.write('D\n')
            msg.flush()
            msg.close()
    else:
        for msg in neighbour_messenger:
            msg.write('a ' +
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
    the neighbour's id
    """
    point_id = int(message.split()[1])
    if point_id > int(own_id):
        res.write(line_blueprint.format(svg_coord(position[0]),
                                        svg_coord(position[1]),
                                        svg_coord(float(message.split()[2])),
                                        svg_coord(float(message.split()[3]))))
        res.flush()
        debug('writing line from '+str(own_id)+' to '+str(point_id)+'\n')


def main():
    """Waits for processes to die around you to check if you can survive
    """
    n_of_neighbours = int(sys.argv[1])
    own_id = int(sys.argv[2])

    # open ressources
    write_main = open('msg_main', 'w')
    messages = open('msg_' + str(own_id), 'r')

    debug('process starting\n')

    neighbours_pid = []

    write_main.write('r')  # tell main we are ready
    write_main.flush()

    # read own coordinates on first line of input
    position = read_position()

    # find neighbours
    neighbours_pid = read_neighbours(n_of_neighbours)
    write_neighbours = [open('msg_' + str(point_id), 'w')
                        for point_id in neighbours_pid]

    dead_processes = 0
    n_of_live_neighbours = n_of_neighbours

    # states
    dead = False
    end = False

    while not(end) or dead_processes < n_of_neighbours:
        if not(dead) and n_of_live_neighbours == 1:
            signal_death(write_neighbours, own_id)
            dead = True

        m = messages.readline()

        if m[0] == 'e':
            end = True
            res = open('result.svg', 'a')
            who_am_i_at_the_end(dead, write_neighbours, own_id, position)

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
                svg_output(m, own_id, position, res)

    res.close()

    debug("And now I am dead.\n")
    write_main.write('e')
    write_main.flush()
    write_main.close()


if __name__ == "__main__":
    main()
