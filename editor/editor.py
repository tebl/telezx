import numpy
import tkinter
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from pprint import pprint

class Editor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("Editor")
        self.create_menu()
        self.zx = ZXScreen()
        self.create_canvas()


    def create_canvas(self):
        self.label = tkinter.Label(self)
        self.label.pack(expand=True)
        self.label.bind('<Motion>', self.mouse_moved)
        self.label.bind('<Button-1>', self.mouse_clicked)
        self.canvas_width = self.zx.SCREEN_WIDTH_CHARS*8
        self.canvas_height = self.zx.SCREEN_HEIGHT_CHARS*8
        self.pixel_data = numpy.full(shape=(self.canvas_height, self.canvas_width, 3), fill_value=0xc0, dtype=numpy.uint8)
        self.update_canvas(auto_refresh=True)


    def update_canvas(self, auto_refresh=True):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

        if auto_refresh:
            self.after(100, self.update_canvas)
        else:
            print("Manually refreshed")


    def create_menu(self):
        self.menu = tkinter.Menu(self)

        file_menu = tkinter.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="New", command=self.file_new)
        file_menu.add_command(label="Open SCR...", command=self.file_open_SCR)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu.add_cascade(label="File", menu=file_menu)

        self.config(menu=self.menu)


    def file_new(self):
        if messagebox.askokcancel(title='New', message='Clear memory?'):
            self.pixel_data[:] = 0xc0
            self.zx.clear_memory()


    def file_open_SCR(self):
        try:
            filename = filedialog.askopenfilename(filetypes=[("SCR", ('*.scr')), ("All files", "*.*")], multiple=False)
            if filename:
                self.zx.flip_memory(numpy.fromfile(filename, dtype='uint8'))
        except Exception as e:
            messagebox.showerror(title='Failed to open file', message=f'Failed with error:\n{e}')


    def mouse_moved(self, event):
        if event.x < self.canvas_width and event.y < self.canvas_height:
            x, y = event.x, event.y
            print('Mouse position: (%s %s)' % (x, y))
            self.pixel_data[y, x] = [0,0,0]
            self.update_canvas(auto_refresh=False)


    def mouse_clicked(self, event):
        x, y = event.x, event.y
        print('Mouse clicked: (%s %s)' % (x, y))



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
        # self.memory = [0] * self.SIZE_MEMORY
        self.memory = numpy.zeros(shape=self.SIZE_MEMORY, dtype=numpy.uint8)
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
        self.memory[:self.SIZE_DATA] = byte
        self.memory[self.SIZE_DATA:] = attribute


    def flip_memory(self, numpy_array):
        if not isinstance(numpy_array, numpy.ndarray) or numpy_array.size != self.SIZE_MEMORY:
            raise ValueError('does not look like a numpy array of expected size')
        self.memory[:] = numpy_array[:]
        print("flipped memory")


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
            self.memory[index + byte_idx*0x100] = byte_value
        if attribute >= self.BLACK:
            self.write_attribute(pos_x, pos_y, attribute)


    def write_attribute(self, pos_x, pos_y, attribute=0):
        self.memory[(pos_y * self.SCREEN_WIDTH_CHARS) + pos_x] = attribute


def main():
    editor = Editor()
    editor.mainloop()


if __name__ == '__main__':
    main()