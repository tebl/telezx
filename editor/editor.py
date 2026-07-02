import numpy
import tkinter

class Editor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("Editor")
        self.createMenu()


    def createMenu(self):
        self.menu = tkinter.Menu(self)

        file_menu = tkinter.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu.add_cascade(label="File", menu=file_menu)

        self.config(menu=self.menu)


    def new_file(self):
        pass


class ZXScreen:
    # Attributes
    BLACK   = 0b00000000
    BLUE    = 0b00000001
    RED     = 0b00000010
    MAGENTA = 0b00000011
    GREEN   = 0b00000100
    CYAN    = 0b00000101
    YELLOW  = 0b00000110
    WHITE   = 0b00000111
    FLASH   = 0b10000000
    BRIGHT  = 0b01000000

    # Screen dimensions
    SCREEN_WIDTH_CHARS = 32
    SCREEN_HEIGHT_CHARS = 24
    SIZE_DATA = 6144
    SIZE_ATTR = 768
    SIZE_MEMORY = SIZE_DATA + SIZE_ATTR

    def __init__(self):
        self.memory = [0] * self.SIZE_MEMORY
        self.cursor_x = 0
        self.cursor_y = 0
        self.__calculate_lookup()


    def __calculate_lookup(self):
        self.start_at = [[0]*self.SCREEN_HEIGHT_CHARS for x in range(self.SCREEN_WIDTH_CHARS)]
        for pos_x in range(0, self.SCREEN_WIDTH_CHARS):
            for pos_y in range(0, self.SCREEN_HEIGHT_CHARS):
                lot = int(pos_y / 2)
                self.start_at[pos_x][pos_y] = (lot * 0x800) + (pos_y - lot*8)*self.SCREEN_WIDTH_CHARS + pos_x


    def clear_memory(self, byte=0, attribute=BLACK):
        for index in range(0, self.SIZE_DATA):
            self.poke(index, byte)
        self.clear_attributes(attribute)


    def clear_attributes(self, attribute=BLACK):
        for index in range(self.SIZE_DATA, self.SIZE_MEMORY):
            self.poke(index, attribute)


    def poke(self, index, value):
        if index >= self.SIZE_MEMORY:
            raise OverflowError(f'index({index}) >= {self.SIZE_MEMORY}')
        self.memory[index] = value

    
    def peek(self, index):
        if index >= self.SIZE_MEMORY:
            raise OverflowError(f'index({index}) >= {self.SIZE_MEMORY}')
        return self.memory[index]


    def to_attribute(self, is_flashing=False, is_bright=False, paper=BLACK, ink=WHITE):
        return (
            (self.FLASH if is_flashing else 0x00) | 
            (self.BRIGHT if is_bright else 0x00) | 
            (paper << 3) |
            ink
        )


    def cursor_next(self):
        self.cursor_x += 1
        if self.cursor_x >= self.SCREEN_WIDTH_CHARS:
            self.cursor_x = 0
            self.cursor_y += 1
            if self.cursor_y >= self.SCREEN_HEIGHT_CHARS:
                self.cursor_y = 0


    def cursor_move(self, pos_x, pos_y):
        self.cursor_x = (pos_x % self.SCREEN_WIDTH_CHARS)
        self.cursor_y = (pos_y % self.SCREEN_HEIGHT_CHARS)


    def cursor_write(self, values, attribute=-1):
        self.write_cell(self.cursor_x, self.cursor_y, values, attribute)
        self.cursor_next()
    

    def write_cell(self, pos_x, pos_y, values, attribute=-1):
        if len(values) != 8:
            raise ValueError(f'values ({values}) not array of 8 bytes')
        index = self.start_at[pos_x][pos_y]
        for byte_idx, byte_value in enumerate(values):
            self.poke(index + byte_idx*0x100, byte_value)
        if attribute >= self.BLACK:
            self.write_attribute(pos_x, pos_y, attribute)


    def write_attribute(self, pos_x, pos_y, attribute=0):
        self.poke(
            (pos_y * self.SCREEN_WIDTH_CHARS) + pos_x,
            attribute
        )


def main():
    editor = Editor()
    editor.mainloop()


if __name__ == '__main__':
    main()