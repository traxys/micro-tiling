#! /usr/bin/python3
import sys
import time


class Interpret:
    """Executes a brainfuck code,
    """
    def __init__(self, file_name, mem_size = 65536, get_input = lambda: sys.stdin.read(1)):
        '''Loads *file_name* and initializes an empty memory of size *mem_size*
        The function *get_input* will be used to read input characters one by one
        '''
        f = open(file_name, "r")
        self.code = [c for c in f.read() if c in '[]+-<>,.']
        self.pos = 0
        self.loop_starts = []
        self.data = bytearray(mem_size)
        self.head_pos = 0
        self.mem_size = mem_size
        self.out = b""
        self.get_input = get_input

    def next_char(self):
        self.pos += 1
        if self.pos >= len(self.code):
            raise EOFError

    def step(self):
        """Execute an instruction
        """
        char = self.code[self.pos]
        if char == '[':
            if self.data[self.head_pos]:
                self.loop_starts.append(self.pos)
            else:
                depth = 1
                while depth > 0:
                    self.next_char()
                    if self.code[self.pos] == "[":
                        depth += 1
                    if self.code[self.pos] == "]":
                        depth -= 1
        if char == ']':
            if self.data[self.head_pos]:
                self.pos = self.loop_starts[-1]
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
        self.next_char()

    def get_output(self, size = 0):
        """If *size* is 0 gets the current output, else execute the code until
        the output size is *size*
        """
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
