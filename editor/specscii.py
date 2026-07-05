import numpy
import tkinter
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from pprint import pprint
from lib import ZXGlyph, ZXFont, ZXScreen

class SPECSCIIEditor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        ttk.Style().theme_use("clam")

        self.title("ZX SPECSCII")
        self.scale = 3
        self.font_default = ZXFont.from_file("font_default.bin")
        self.create_menu()
        self.zx = ZXScreen()
        self.zx.flip_memory(numpy.fromfile("test.scr", dtype='uint8'))

        self.view = Editor(self, self.zx)
        self.view.pack(expand=True)

        self.highlight = Sidebar(self)
        self.highlight.pack(fill=tkinter.Y, expand=True)

        self.sequence = List(self)
        self.sequence.pack(fill=tkinter.X, expand=True)

        # self.view.grid(row=0, column=0)
        # self.highlight.grid(row=0, column=1, padx=10, sticky="n")




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
        self.view.update_scale()
        self.highlight.update_scale()

    def set_scale_1x(self):
        self.set_scale(1)

    def set_scale_2x(self):
        self.set_scale(2)

    def set_scale_3x(self):
        self.set_scale(3)


class Editor(tkinter.Label):
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


class Sidebar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.button = ttk.Button(self, text="test")
        self.pack()

class List(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.treeview = ttk.Treeview(columns=("Entry", "Data"))
        self.treeview.heading("Entry", text="Description")
        self.treeview.heading("Data", text="Data")
        # self.treeview.pack(padx=10, pady=10, expand=True, fill=tkinter.BOTH)

        self.scrollbar = ttk.Scrollbar(self, orient=tkinter.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.scrollbar.set)
        # self.pack(fill=tkinter.X, expand=True, padx=10, pady=10)

class Highlight(tkinter.Label):
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


def main():
    editor = SPECSCIIEditor()
    editor.mainloop()


if __name__ == '__main__':
    main()