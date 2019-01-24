#! /usr/bin/python3
import curses
import sys
from math import ceil


class Interpret:
    def __init__(self, file_name, mem_size, get_input = lambda: sys.stdin.read(1)):
        f = open(file_name, "r")
        self.lines = [line.split('#')[0] for line in f.read().split("\n")]
        self.pos = [0,0]#line, column
        self.loop_starts = []
        self.data = bytearray(mem_size)
        self.head_pos = 0
        self.mem_size = mem_size
        self.out = ""
        self.get_input = get_input
        self.correct_pos()
    def correct_pos(self):
        while self.pos[1]>=len(self.lines[self.pos[0]]):
            self.pos = [self.pos[0]+1, self.pos[1]-len(self.lines[self.pos[0]])]
            if self.pos[0]>=len(self.lines):
                raise EOFError()
    def step(self):
        char = self.lines[self.pos[0]][self.pos[1]]
        if char == '[':
            if self.data[self.head_pos]:
                self.loop_starts.append(self.pos[:])
            else:
                depth = 1
                while depth > 0:
                    self.pos[1] += 1
                    self.correct_pos()
                    if self.lines[self.pos[0]][self.pos[1]] == "[":
                        depth += 1
                    if self.lines[self.pos[0]][self.pos[1]] == "]":
                        depth -= 1
        if char == ']':
            if self.data[self.head_pos]:
                self.pos = self.loop_starts[-1][:]
            else:
                self.loop_starts.pop(-1)
        if char == '>':
            self.head_pos += 1
            self.head_pos %= self.mem_size
        if char == '<':
            self.head_pos -= 1
            self.head_pos %= self.mem_size
        if char == '+':
            self.data[self.head_pos] = (self.data[self.head_pos] + 1)%256
        if char == '-':
            self.data[self.head_pos] = (self.data[self.head_pos] - 1)%256
        if char == '.':
            self.out += chr(self.data[self.head_pos])
        if char == ',':
            self.data[self.head_pos] = ord(self.get_input())
        self.pos[1] += 1
        self.correct_pos()
    def get_output(self):
        out = self.out
        self.out = ""
        return out
    def set_input(self, string):
        self.input += string

def interactive_mode(stdscr, file_name, mem_size, delay):
    curses.curs_set(0)
    height, width = stdscr.getmaxyx()
    program = Interpret(file_name, mem_size, lambda : chr(stdscr.getch()))
    block_width = 2
    if width <= 2*block_width+2:
        raise StandardError("terminal too thin for interactive mode")
    code_width = max(len(l) for l in program.lines)
    code_height = len(program.lines)
    mem_width = max(width/2, width-code_width)
    mem_col = max(1,int(mem_width/(block_width+1)))
    mem_width = mem_col*(block_width+1)-1
    mem_height = ceil(mem_size/mem_col)
    mem_pad = curses.newpad(mem_height, mem_width)
    terminal_height = max(5, height-mem_height)

    code_pad = curses.newpad(code_height, code_width)
    hexa = lambda k: hex(k)[-2:].replace('x', ' ').upper()
    for l,line in enumerate(program.lines):
        if l == program.pos[0]:
            for c in range(len(line)):
                if c == program.pos[1]:
                    code_pad.addstr(l,c, line[c], curses.A_REVERSE)
                else:
                    code_pad.addstr(l,c, line[c])
        else:
            code_pad.addstr(l,0,line)
    for k in range(mem_size):
        l, c = divmod(k, mem_col)
        c *= block_width +1
        if k == program.head_pos:
            mem_pad.addstr(l, c, hexa(program.data[k]), curses.A_REVERSE)
        else:
            mem_pad.addstr(l, c, hexa(program.data[k]))
    last_pos = program.pos[:]
    last_head_pos = program.head_pos
    while True:
        for k in [last_head_pos, program.head_pos]:
            l, c = divmod(k, mem_col)
            c *= block_width +1
            if k == program.head_pos:
                mem_pad.addstr(l, c, hexa(program.data[k]), curses.A_REVERSE)
            else:
                mem_pad.addstr(l, c, hexa(program.data[k]))
        code_pad.addstr(last_pos[0], last_pos[1], program.lines[last_pos[0]][last_pos[1]])
        code_pad.addstr(program.pos[0], program.pos[1], program.lines[program.pos[0]][program.pos[1]], curses.A_REVERSE)
        stdscr.refresh()
        code_pad_start_l = max(0, min(code_height-height, program.pos[0]-height//2))
        code_pad_start_c = max(0, min(code_width-width+mem_width, program.pos[1]-(width-mem_width)//2))
        code_pad.noutrefresh(code_pad_start_l,code_pad_start_c, 0,0, height-1, width-mem_width-1)
        mem_pad_start_l = max(0, min(mem_height-(height-terminal_height), program.head_pos//mem_col-(height-terminal_height)//2))
        mem_pad.noutrefresh(mem_pad_start_l,0, terminal_height, width-mem_width, height-1, width-1)
        curses.doupdate()
        last_pos = program.pos[:]
        last_head_pos = program.head_pos
        try:
            program.step()
        except EOFError:
            return
        time.sleep(delay)
        #stdscr.getch()



if __name__ == "__main__":
    import time
    mem_size = 65536#1024
    delay = 0
    if "-n" in sys.argv:
        i = sys.argv.index("-n")
        mem_size = int(sys.argv.pop(i+1))
        sys.argv.pop(i)
    if "-d" in sys.argv:
        i = sys.argv.index("-d")
        delay = float(sys.argv.pop(i+1))/1000
        sys.argv.pop(i)
    if "-i" in sys.argv:
        #interactive mode
        i = sys.argv.index("-i")
        sys.argv.pop(i)
        curses.wrapper(interactive_mode, sys.argv[1], mem_size, delay)
        exit()
    # fast interpreting
    file_name = sys.argv[1]
    program = Interpret(file_name, mem_size)
    while True:
        sys.stdout.write(program.get_output())
        sys.stdout.flush()
        try:
            program.step()
        except TypeError:
            break
        time.sleep(delay)
    sys.stdout.write(program.get_output())
    sys.stdout.write("\n")
    sys.stdout.flush()
