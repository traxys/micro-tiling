#! /usr/bin/python3
import curses
import sys
import time


class Interpret:
    def __init__(self, file_name, mem_size = 65536, get_input = lambda: sys.stdin.read(1)):
        f = open(file_name, "r")
        self.lines = [line for line in f.read()]
        self.pos = [0,0]#line, column
        self.loop_starts = []
        self.data = bytearray(mem_size)
        self.head_pos = 0
        self.mem_size = mem_size
        self.out = b""
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
            self.out += bytes([self.data[self.head_pos]])
        if char == ',':
            self.data[self.head_pos] = ord(self.get_input())
        self.pos[1] += 1
        self.correct_pos()
    def get_output(self, size = 0):
        if size <= 0:
            out = self.out
            self.out = b""
            return out
        else:
            try:
                while len(self.out)<size:
                    self.step()
            except EOFError:
                out = self.out
                if out != b"":
                    self.out = b""
                    return out
                else:
                    raise
            out = self.out
            self.out = b""
            return out
    def set_input(self, string):
        self.input += string


if __name__ == "__main__":
    mem_size = 65536
    if "-n" in sys.argv:
        i = sys.argv.index("-n")
        mem_size = int(sys.argv.pop(i+1))
        sys.argv.pop(i)
    try:
        file_name = sys.argv[1]
    except IndexError:
        print('missing argument')
        print('usage : bf_interpreter.py [options] brainfuck_file')
        print('options :')
        print('-n (number)  -> set memory size')
        raise
    program = Interpret(file_name, mem_size)
    while True:
        try:
            sys.stdout.buffer.write(program.get_output(1))
        except EOFError:
            break
        sys.stdout.flush()
    sys.stdout.flush()
