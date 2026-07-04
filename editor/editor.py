import numpy
import tkinter
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from pprint import pprint

class Editor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZX Editor")
        self.scale = 3
        self.font_default = ZXFont.from_file("font_default.bin")
        self.create_menu()
        self.zx = ZXScreen()
        self.zx.flip_memory(numpy.fromfile("test.scr", dtype='uint8'))

        self.view = EditorView(self, self.zx)
        self.highlight = EditorHighlight(self)

        self.view.grid(row=0, column=0)
        self.highlight.grid(row=0, column=1, padx=10, sticky="n")


    def create_menu(self):
        self.menu = tkinter.Menu(self)

        file_menu = tkinter.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="New", command=self.file_new)
        file_menu.add_command(label="Open SCR...", command=self.file_open_SCR)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu.add_cascade(label="File", menu=file_menu)

        view_menu = tkinter.Menu(self.menu, tearoff=0)
        scale_menu = tkinter.Menu(view_menu, tearoff=0)
        scale_menu.add_command(label="1x", command=self.set_scale_1x)
        scale_menu.add_command(label="2x", command=self.set_scale_2x)
        scale_menu.add_command(label="3x", command=self.set_scale_3x)
        view_menu.add_cascade(label="Scale", menu=scale_menu)
        self.menu.add_cascade(label="View", menu=view_menu)

        self.config(menu=self.menu)


    def file_new(self):
        if messagebox.askokcancel(title='New', message='Clear memory?'):
            self.view.clear()
            self.zx.clear_memory()


    def file_open_SCR(self):
        try:
            filename = filedialog.askopenfilename(filetypes=[("SCR", ('*.scr')), ("All files", "*.*")], multiple=False)
            if filename:
                self.zx.flip_memory(numpy.fromfile(filename, dtype='uint8'))
        except Exception as e:
            messagebox.showerror(title='Failed to open file', message=f'Failed with error:\n{e}')


    def set_scale(self, value):
        self.scale = value
        print(f"set scale {value}")
        self.view.update_scale()
        self.highlight.update_scale()

    def set_scale_1x(self):
        self.set_scale(1)

    def set_scale_2x(self):
        self.set_scale(2)

    def set_scale_3x(self):
        self.set_scale(3)


class EditorView(tkinter.Label):
    def __init__(self, editor, zx_screen):
        super().__init__(editor)
        self.editor = editor
        self.zx = zx_screen
        self.bind('<Motion>', self.mouse_moved)
        self.bind('<Button-1>', self.mouse_clicked)
        self.view_width = self.zx.SCREEN_WIDTH_PIXELS
        self.view_height = self.zx.SCREEN_HEIGHT_PIXELS
        self.pixel_data = numpy.full(shape=(self.view_height*self.editor.scale, self.view_width*self.editor.scale, 3), fill_value=0, dtype=numpy.uint8)
        self.update_view(auto_refresh=True)

    def clear(self):
        self.pixel_data[:] = 0

    def mouse_moved(self, event):
        pass

    def mouse_clicked(self, event):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            char_x = (event.x // self.editor.scale) // 8
            char_y = (event.y // self.editor.scale) // 8
            self.editor.highlight.set_region(self, char_x, char_y)
            self.update_view(auto_refresh=False)

    def render_canvas(self):
        rgb_data = self.zx.to_rgb()
        rgb_data = numpy.repeat(numpy.repeat(rgb_data, self.editor.scale, axis=0), self.editor.scale, axis=1)
        self.pixel_data[:] = rgb_data

    def update_view(self, auto_refresh=True):
        self.render_canvas()
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.config(image=tk_img)
        self.image = tk_img

        if auto_refresh:
            self.after(100, self.update_view)

    def update_scale(self):
        self.pixel_data = numpy.full(shape=(self.view_height*self.editor.scale, self.view_width*self.editor.scale, 3), fill_value=0, dtype=numpy.uint8)
        self.update_view(auto_refresh=False)


class EditorHighlight(tkinter.Label):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.view_width = 8
        self.view_height = 8
        self.scale = 8

        self.update_scale(refresh=False)
        self.update_view(auto_refresh=True)

    def update_scale(self, refresh=True):
        self.actual_width = self.view_width * self.editor.scale * self.scale
        self.actual_height = self.view_height * self.editor.scale * self.scale
        self.pixel_data = numpy.full(shape=(self.actual_height, self.actual_width, 3), fill_value=0, dtype=numpy.uint8)
        if refresh:
            self.update_view(auto_refresh=False)

    def update_view(self, auto_refresh=True):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.config(image=tk_img)
        self.image = tk_img

        if auto_refresh:
            self.after(100, self.update_view)

    
    def set_region(self, source, char_x, char_y):
        region_size = 8*self.editor.scale
        start_x = char_x * region_size
        start_y = char_y * region_size

        result = source.pixel_data[start_y:(start_y+region_size), start_x:(start_x+region_size)]
        result = numpy.repeat(numpy.repeat(result, self.scale, axis=0), self.scale, axis=1)

        self.pixel_data[:] = result


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
    SCREEN_WIDTH_PIXELS = SCREEN_WIDTH_CHARS*8
    SCREEN_HEIGHT_CHARS = 24
    SCREEN_HEIGHT_PIXELS = SCREEN_HEIGHT_CHARS*8
    SIZE_DATA = 6144
    SIZE_ATTR = 768
    SIZE_MEMORY = SIZE_DATA + SIZE_ATTR

    def __init__(self):
        self.memory = numpy.zeros(shape=self.SIZE_MEMORY, dtype=numpy.uint8)
        self.cursor_x = 0
        self.cursor_y = 0
        self.__calculate_lookup()


    def __calculate_lookup(self):
        self.start_at = [[0]*self.SCREEN_HEIGHT_CHARS for x in range(self.SCREEN_WIDTH_CHARS)]
        for pos_x in range(0, self.SCREEN_WIDTH_CHARS):
            for pos_y in range(0, self.SCREEN_HEIGHT_CHARS):
                lot = pos_y // 8
                self.start_at[pos_x][pos_y] = (lot * 0x800) + (pos_y - lot*8)*self.SCREEN_WIDTH_CHARS + pos_x


    def clear_memory(self, byte=0, attribute=BLACK):
        self.memory[:self.SIZE_DATA] = byte
        self.memory[self.SIZE_DATA:] = attribute


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


    def to_rgb(self):
        pixels = numpy.zeros(shape=(self.SCREEN_HEIGHT_PIXELS, self.SCREEN_WIDTH_PIXELS, 3), dtype=numpy.uint8)
        for pos_x in range(self.SCREEN_WIDTH_CHARS):
            for pos_y in range(self.SCREEN_HEIGHT_CHARS):
                attr_idx = self.SIZE_DATA + (self.SCREEN_WIDTH_CHARS*pos_y + pos_x)
                attr_value = self.__parse_attribute(self.memory[attr_idx])

                data_start = self.start_at[pos_x][pos_y]
                for line in range(8):
                    data_idx = data_start + (line * 0x100)
                    data_value = self.memory[data_idx]
                    for bit_idx in range(8):
                        pixels[pos_y*8 + line, pos_x*8 + bit_idx] = self.__map_to_rgb(
                            self.__check_bits(data_value, bit_idx),
                            attr_value
                        )
        return pixels


    def __parse_attribute(self, attribute):
        return {
            'flash': (attribute & self.FLASH) == self.FLASH,
            'bright': (attribute & self.BRIGHT) == self.BRIGHT,
            'paper': (attribute & 0b00111000) >> 3,
            'ink': attribute & 0b00000111
        }


    def __map_to_rgb(self, is_on, attr_value):
        colour = attr_value['ink'] if is_on else attr_value['paper']
        value = 255 if attr_value['bright'] else 224
        return [
            ((colour >> 1) & 1)*value,  # red
            ((colour >> 2) & 1)*value,  # green
            (colour & 1)*value          # blue
        ]


    def __check_bits(self, value, bit_idx):
        mask = (1 << (7 - bit_idx))
        return (value & mask) != 0


    def write_cell(self, pos_x, pos_y, values, attribute=-1):
        if values.size != 8:
            raise ValueError(f'values ({values}) not array of 8 bytes')
        index = self.start_at[pos_x][pos_y]
        for byte_idx, byte_value in enumerate(values):
            self.memory[index + byte_idx*0x100] = byte_value
        if attribute >= self.BLACK:
            self.write_attribute(pos_x, pos_y, attribute)


    def write_attribute(self, pos_x, pos_y, attribute=0):
        self.memory[(pos_y * self.SCREEN_WIDTH_CHARS) + pos_x] = attribute


class ZXFont:
    def __init__(self, font_data):
        self.font_data = font_data

    def get_offset(self, offset):
        return self.font_data[offset]

    def get_character(self, character):
        data = self.get_offset(ord(character) - 32)
        return data

    @classmethod
    def from_file(cls, path):
        font_data = numpy.fromfile(path, dtype=numpy.uint8)
        font_data = numpy.reshape(font_data, shape=(96,8))
        return cls(font_data)

def main():
    editor = Editor()
    editor.mainloop()


if __name__ == '__main__':
    main()