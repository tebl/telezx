from datetime import datetime
from random import choices
import ttkbootstrap as ttk
from ttkbootstrap.style import Bootstyle
from tkinter.filedialog import askdirectory
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
from pathlib import Path
import numpy

from lib import ZXScreen, ZXFont, ZXGlyph
from PIL import Image, ImageTk


class ZXEditor(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.__load_assets()

        self.scale = 3
        self.is_grid_enabled = True

        self.zx_screen = ZXScreen()
        self.zx_screen.flip_memory(numpy.fromfile("test.scr", dtype='uint8'))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)

        self.menu = Menu(self)
        self.menu.grid(row=0, column=0, columnspan=3, sticky=EW)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=1, column=1, sticky=NE)

        self.main = Main(self)
        self.main.grid(row=1, column=0, sticky=NW)

        self.status = Status(self)
        self.status.grid(row=3, column=0, columnspan=3, sticky=EW)

    def toggle_grid_enabled(self):
        self.is_grid_enabled = (not self.is_grid_enabled)
        print(self.is_grid_enabled)
        self.main.configure_scale(self.scale)

    def changed_grid_enabled(self, value):
        self.is_grid_enabled = value
        self.main.configure_scale(self.scale)

    def clicked_new(self):
        print("Clear")

    def clicked_scr(self):
        print("Open SCR")

    def set_scale(self, value):
        self.scale = value
        # self.sidebar.highlight.configure_scale(value)
        # self.sidebar.symbols.configure_scale(value)
        self.main.configure_scale(value)

    def refresh(self):
        self.main.refresh()

    def __load_assets(self):
        image_files = {
            'new-dark': 'icons8_add_folder_24px.png',
            'new-light': 'icons8_add_book_24px.png',

            'settings-dark': 'icons8_settings_24px.png',
            'settings-light': 'icons8_settings_24px_2.png',
            'stop-backup-dark': 'icons8_cancel_24px.png',
            'stop-backup-light': 'icons8_cancel_24px_1.png',
            'stop-dark': 'icons8_stop_24px.png',
            'stop-light': 'icons8_stop_24px_1.png',
            'opened-folder': 'icons8_opened_folder_24px.png',
            'open': 'icons8_folder_24px.png'
        }

        self.photoimages = []
        imgpath = Path(__file__).parent / 'assets'
        for key, val in image_files.items():
            _path = imgpath / val
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))


class Menu(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='primary.TFrame')
        self.zx_editor = master

        ## New...
        btn = ttk.Button(
            master=self,
            text='New...',
            image='new-light', 
            compound=LEFT, 
            command=self.master.clicked_new
        )
        btn.grid(row=0, column=0)

        ## Open SCR...
        btn = ttk.Button(
            master=self, 
            text='Open SCR', 
            image='opened-folder', 
            compound=LEFT, 
            command=self.master.clicked_scr
        )
        btn.grid(row=0, column=1)

        ## configure scale
        scale_options = ttk.Menu(self)
        scale_options.add_radiobutton(label="1x", command=lambda: self.set_scale(1))
        scale_options.add_radiobutton(label="2x", command=lambda: self.set_scale(2))
        scale_options.add_radiobutton(label="3x", command=lambda: self.set_scale(3))
        scale_options.add_radiobutton(label="4x", command=lambda: self.set_scale(4))
        self.scale = ttk.Menubutton(
            master=self,
            text="Set scale",
            menu=scale_options
        )
        self.scale.grid(row=0, column=2)

        ## Enable display grid
        btn = ttk.Button(
            master=self, 
            text='Grid', 
            image='opened-folder', 
            compound=LEFT, 
            command=self.zx_editor.toggle_grid_enabled
        )
        btn.grid(row=0, column=3)

    def set_scale(self, value):
        self.scale.config(text=f'{value}x')
        self.master.set_scale(value)


class Canvas(ttk.Frame):
    SCALE_MASTER = 0

    def __init__(self, master, zx_editor, view_width, view_height, default_fill=0, style='bg.TFrame', scale_mode=0, label_padx=5, label_pady=5):
        super().__init__(master, style=style)
        self.zx_editor = zx_editor
        self.default_fill = default_fill
        self.view_width = view_width
        self.view_height = view_height
        self.scale_mode = scale_mode

        self.label = ttk.Label(self)
        self.label.pack(padx=label_padx, pady=label_pady)

        self.configure_scale(self.zx_editor.scale)

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def configure_scale(self, value):
        # Canvas can add additional scaling in addition to that of the main
        # application, should be an integer value
        self.scale_value = self.get_scale(value)
        self.pixel_data = numpy.full(shape=(self.view_height*self.scale_value, self.view_width*self.scale_value, 3), fill_value=self.default_fill, dtype=numpy.uint8)
        self.flip_canvas()

    def get_scale(self, value):
        scaling = self.scale_mode
        if self.scale_mode == self.SCALE_MASTER:
            scaling = value
        return scaling

    def flip_canvas(self):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

    def render_rgb(self, rgb_data):
        rgb_data = numpy.repeat(numpy.repeat(rgb_data, self.scale_value, axis=0), self.scale_value, axis=1)
        self.pixel_data[:] = rgb_data


class Main(ttk.Frame):
    NOGRID_Y_OFFSET = 2

    def __init__(self, master):
        super().__init__(master)
        self.zx_editor = master
        self.default_fill = colorutils.color_to_rgb(master.master.style.colors.get('bg'))
        self.grid_colour = colorutils.color_to_rgb(master.master.style.colors.get('dark'))
        self.highlight_colour = colorutils.color_to_rgb(master.master.style.colors.get('danger'))
        self.cursor_x = -1
        self.cursor_y = -1
        self.label = ttk.Label(self)
        self.label.pack(padx=5, pady=5)


        self.configure_scale(self.zx_editor.scale)
        self.label.bind('<Motion>', self.mouse_moved)
        self.label.bind('<Button-1>', self.mouse_clicked)

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def create(self):
        colour = self.grid_colour if self.zx_editor.is_grid_enabled else self.default_fill
        self.pixel_data = numpy.full(shape=(self.__get_canvas_height(), self.__get_canvas_width(), 3), fill_value=colour, dtype=numpy.uint8)

    def __get_canvas_width(self):
        num_pixels = ZXScreen.SCREEN_WIDTH_CHARS*8*self.zx_editor.scale
        num_pixels += ZXScreen.SCREEN_WIDTH_CHARS+1
        return num_pixels

    def __get_canvas_height(self):
        num_pixels = ZXScreen.SCREEN_HEIGHT_CHARS*8*self.zx_editor.scale
        num_pixels += ZXScreen.SCREEN_HEIGHT_CHARS+1
        return num_pixels

    def configure_scale(self, scale_value):
        self.create()
        self.refresh()

    def flip_canvas(self):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

    def refresh(self):
        self.pixel_data[:] = self.grid_colour if self.zx_editor.is_grid_enabled else self.default_fill

        rgb_data = self.master.zx_screen.to_rgb()
        rgb_data = numpy.repeat(numpy.repeat(rgb_data, self.zx_editor.scale, axis=0), self.zx_editor.scale, axis=1)
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.__refresh_cell(char_x, char_y, rgb_data)
        self.__highlight_cell(self.cursor_x, self.cursor_y, self.highlight_colour)
        self.flip_canvas()

    def __refresh_cell(self, char_x, char_y, rgb_data):
        pix_x, pix_y, pix_size = self.__get_canvas_position(char_x, char_y)
        rgb_x, rgb_y, rgb_size = self.__get_screen_position(char_x, char_y)
        self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = rgb_data[rgb_y:rgb_y+rgb_size, rgb_x:rgb_x+rgb_size]

    def __highlight_cell(self, char_x, char_y, colour):
        if char_x == -1 or char_y == -1:
            return
        pix_x, pix_y, pix_size = self.__get_canvas_position(char_x, char_y)
        self.pixel_data[pix_y-1, pix_x-1:pix_x+pix_size+1] = colour
        self.pixel_data[pix_y+pix_size, pix_x-1:pix_x+pix_size+1] = colour
        self.pixel_data[pix_y-1:pix_y+pix_size, pix_x-1] = colour
        self.pixel_data[pix_y-1:pix_y+pix_size, pix_x+pix_size] = colour

        # average RGB 
        fill = numpy.full(shape=(pix_size, pix_size, 3), fill_value=colour, dtype=numpy.uint8)
        self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = numpy.mean(numpy.array([self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size], fill]), axis=0)

        # darken contents
        # self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] >> 1


    def __get_screen_position(self, char_x, char_y):
        cell_size = 8*self.zx_editor.scale
        x = char_x*cell_size
        y = char_y*cell_size
        return (x, y, cell_size)

    def __get_canvas_position(self, char_x, char_y):
        '''
        Translate from cursor location to pixel ranges within the displayed canvas,
        adjusted for whether a 1px wide grid is enabled. If not enabled then we
        will instead try to center image within canvas.
        '''
        cell_size = 8*self.zx_editor.scale
        x = char_x*cell_size
        y = char_y*cell_size
        if self.zx_editor.is_grid_enabled:
            x += char_x + 1
            y += char_y + 1
        else:
            x += ZXScreen.SCREEN_WIDTH_CHARS // 2
            y+= self.NOGRID_Y_OFFSET
        return (x, y, cell_size)

    def __get_cursor_from(self, pos_x, pos_y):
        '''
        Translates a pixel location within the displayed canvas to cursor location.
        '''
        cell_size = 8*self.zx_editor.scale
        if self.zx_editor.is_grid_enabled:
            char_x = ((pos_x - 1) // (cell_size + 1)) if pos_x >= 1 else 0
            char_y = ((pos_y - 1) // (cell_size + 1)) if pos_y >= 1 else 0
            return (char_x, char_y)

        char_x = ((pos_x - (ZXScreen.SCREEN_WIDTH_CHARS // 2)) // cell_size)
        if char_x < 0 or char_x >= ZXScreen.SCREEN_WIDTH_CHARS:
            char_x = -1

        char_y = ((pos_y - self.NOGRID_Y_OFFSET) // cell_size)
        if char_y < 0 or char_y >= ZXScreen.SCREEN_HEIGHT_CHARS:
            char_y = -1
        return (char_x, char_y)

    def mouse_moved(self, event):
        # if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
        #     char_x, char_y = self.__get_cursor_from(event.x, event.y)
        #     self.__highlight_cell(char_x, char_y, self.HIGHLIGHT_ACTIVE)
        #     self.refresh()
        pass

    def mouse_clicked(self, event):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            new_x, new_y = self.__get_cursor_from(event.x, event.y)
            if new_x >= 0 and new_y >= 0:
                self.cursor_x = new_x
                self.cursor_y = new_y
                print(self.cursor_x, self.cursor_y)
                attr = self.zx_editor.zx_screen.get_attribute_at(self.cursor_x, self.cursor_y)
                self.zx_editor.sidebar.palette.set_attribute(attr)
                self.refresh()


class Sidebar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # self.highlight = Highlight(master=self, zx_editor=master)
        # self.highlight.pack(fill=X, pady=0)

        self.palette = Palette(master=self, zx_editor=master)
        self.palette.pack(fill=X, pady=0)

        self.symbols = Symbols(self, zx_editor=master)
        self.symbols.pack(fill=X, pady=0)


class Palette(ttk.Frame):
    def __init__(self, master, zx_editor):
        super().__init__(master, style='bg.TFrame')
        self.zx_editor = zx_editor
        self.is_bright = False
        self.is_bright_var = ttk.BooleanVar(master=self, value=self.is_bright)
        self.is_flash = False
        self.is_flash_var = ttk.BooleanVar(master=self, value=self.is_flash)
        self.is_sticky = False
        self.is_sticky_var = ttk.BooleanVar(master=self, value=self.is_sticky)
        self.current_ink = ZXScreen.WHITE
        self.current_paper = ZXScreen.BLACK

        lbl = ttk.Label(self, text="INK")
        lbl.grid(row=0, column=0)
        self.ink_widgets = []

        frame = ttk.Frame(self)
        frame.grid(row=1, column=0)
        for ink_value in range(ZXScreen.BLACK, (ZXScreen.WHITE + 1)):
            widget = PaletteColour(frame, self.zx_editor, self, type=PaletteColour.TYPE_INK, colour=ink_value)
            widget.grid(row=ink_value, column=0, padx=0, pady=0)
            widget.refresh()
            self.ink_widgets.append(widget)


        lbl = ttk.Label(self, text="PAPER")
        lbl.grid(row=0, column=1)
        self.paper_widgets = []

        frame = ttk.Frame(self, style="danger.TFrame")
        frame.grid(row=1, column=1)
        for ink_value in range(ZXScreen.BLACK, (ZXScreen.WHITE + 1)):
            widget = PaletteColour(frame, self.zx_editor, self, type=PaletteColour.TYPE_PAPER, colour=ink_value)
            widget.grid(row=ink_value, column=0, padx=0, pady=0)
            widget.refresh()
            self.ink_widgets.append(widget)


        # lbl = ttk.Label(self, text="Modifier")
        # lbl.grid(row=0, column=2, sticky=N)

        frame = ttk.Frame(self)
        frame.grid(row=1, column=2, sticky=NSEW)
        btn = ttk.Checkbutton(
            frame, 
            text="Bright", 
            bootstyle="square-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_bright_var,
            command=lambda: self.changed_bright(self.is_bright_var.get()))
        btn.grid(row=0, column=0, sticky=NW, padx=20)

        btn = ttk.Checkbutton(
            frame, 
            text="Flashing", 
            bootstyle="square-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_flash_var,
            command=lambda: self.changed_flash(self.is_flash_var.get()))
        btn.grid(row=1, column=0, sticky=NW, padx=20)

        btn = ttk.Checkbutton(
            frame, 
            text="Keep attribute", 
            bootstyle="danger-round-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_sticky_var,
            command=lambda: self.changed_sticky(self.is_sticky_var.get()))
        btn.grid(row=5, column=0, sticky=NW, padx=20, pady=(10, 0))

    def changed_bright(self, value):
        self.is_bright = value
        self.refresh()

    def changed_flash(self, value):
        self.is_flash = value
        self.refresh()

    def changed_sticky(self, value):
        self.is_sticky = value
        self.refresh()

    def set_attribute(self, value):
        parsed = ZXScreen.to_parsed_attribute(value)
        self.is_bright = parsed['bright']
        self.is_flash = parsed['flash']
        self.current_ink = parsed['ink']
        self.current_paper = parsed['paper']
        self.refresh()

    def set_ink(self, colour):
        self.current_ink = colour
        self.refresh()

    def set_paper(self, colour):
        self.current_paper = colour
        self.refresh()

    def refresh(self):
        self.is_bright_var.set(self.is_bright)
        self.is_flash_var.set(self.is_flash)
        for widget in self.ink_widgets:
            widget.refresh()
        for widget in self.paper_widgets:
            widget.refresh()


class PaletteColour(Canvas):
    TYPE_INK = 0
    TYPE_PAPER = 1

    def __init__(self, master, zx_editor, palette, type, colour):
        super().__init__(master, zx_editor, view_width=8, view_height=8, scale_mode=0, label_padx=0, label_pady=0)
        self.palette = palette
        self.type = type
        self.colour = colour
        self.label.bind('<Button-1>', self.mouse_clicked)

    def mouse_clicked(self, event):
        if self.type == self.TYPE_INK:
            self.palette.set_ink(self.colour)
        if self.type == self.TYPE_PAPER:
            self.palette.set_paper(self.colour)

    def refresh(self):
        zx_fg = ZXScreen.colour_to_rgb(self.colour, self.palette.is_bright)
        inactive = colorutils.color_to_rgb(self.zx_editor.master.style.colors.get('dark'))

        rgb_data = numpy.full(shape=(8, 8, 3), fill_value=zx_fg, dtype=numpy.uint8)
        rgb_data[1:7, 1:7] = inactive
        if self.__check_active():
            rgb_data[2:6, 2:6] = zx_fg

        self.render_rgb(rgb_data)
        self.flip_canvas()

    def __check_active(self):
        if self.type == self.TYPE_INK and self.palette.current_ink == self.colour:
            return True
        if self.type == self.TYPE_PAPER and self.palette.current_paper == self.colour:
            return True
        return False

    

class Highlight(ttk.Frame):
    def __init__(self, master, zx_editor):
        super().__init__(master, style='bg.TFrame')
        self.zx_editor = zx_editor
        self.pixel_frame = ttk.Frame(self, padding=5, style="bg.TFrame")
        self.pixel_frame.pack()

        self.create_widgets()

    def create_widgets(self):
        self.widgets = {}
        for pixel_row in range(8):
            for pixel_column in range(8):
                widget = Glyph(self.pixel_frame, self.zx_editor, (pixel_column, pixel_row))
                widget.grid(row=pixel_row, column=pixel_column, padx=0, pady=0)
                widget.render_rgb(numpy.zeros(shape=(8, 8, 3), dtype=numpy.uint8))
                widget.flip_canvas()
                self.widgets[(pixel_row, pixel_column)] = widget

    def configure_scale(self, value):
        for pixel_row in range(8):
            for pixel_column in range(8):
                self.widgets[(pixel_row, pixel_column)].configure_scale(value)


class Symbols(ttk.Frame):
    NUM_COLUMNS = 8

    def __init__(self, master, zx_editor):
        super().__init__(master, style='bg.TFrame')
        self.zx_editor = zx_editor

        self.font_frame = ttk.Frame(self, padding=5, style="bg.TFrame")
        self.font_frame.pack()
        self.font_widgets = []
        self.load_font('font_default.bin', self.font_frame, self.font_widgets)

        self.glyph_frame = ttk.Frame(self, padding=5, style="bg.TFrame")
        self.glyph_frame.pack()
        self.glyph_widgets = []
        self.load_font('font_glyphs.bin', self.glyph_frame, self.glyph_widgets)


    def configure_scale(self, value):
        self.load_font('font_default.bin', self.font_frame, self.font_widgets)
        self.load_font('font_glyphs.bin', self.glyph_frame, self.glyph_widgets)


    def load_font(self, path, frame, widgets):
        font_data = ZXFont.from_file(path, rgb_fg=self.__get_colour('fg'), rgb_bg=self.__get_colour('bg'))
        
        # Remove existing elements
        for widget in widgets:
            widget.destroy()
        widgets.clear()

        # Add new ones
        grid_row = 0
        grid_column = 0
        for idx in range(font_data.get_glyph_count()):
            widget = Glyph(frame, self.zx_editor, idx)
            widget.render_rgb(font_data.get_offset_rgb(idx))
            widget.flip_canvas()
            widget.grid(row=grid_row, column=grid_column, padx=0, pady=0)

            grid_column += 1
            if grid_column == self.NUM_COLUMNS:
                grid_column = 0
                grid_row += 1
            widgets.append(widget)
    

    def __get_colour(self, color_label):
        return colorutils.color_to_rgb(self.zx_editor.master.style.colors.get(color_label))


class Glyph(Canvas):
    def __init__(self, master, zx_editor, glyph_idx):
        super().__init__(master, zx_editor, view_width=8, view_height=8, scale_mode=0, label_padx=0, label_pady=0)
        self.glyph_idx = glyph_idx
        self.label.bind('<Button-1>', self.mouse_clicked)
        self.label.bind('<Enter>', self.mouse_hover)
        self.label.bind('<Leave>', self.mouse_exit)

    def mouse_clicked(self, event):
        print('Clicked', self.glyph_idx)

    def mouse_hover(self, event):
        self.label.config(relief='raised')

    def mouse_exit(self, event):
        self.label.config(relief='flat')


class Status(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='dark.TFrame')
        self.columnconfigure(2, weight=1)

        self.position = ttk.Label(
            master=self,
            textvariable='status-position',
            bootstyle="inverse-dark"
        )
        self.position.grid(row=0, column=0)
        self.set_position(0, 0)

        self.status = ttk.Label(
            master=self,
            textvariable='status-text',
            bootstyle="inverse-dark"
        )
        self.status.grid(row=0, column=1)
        self.set_status('')

    def set_position(self, pos_x, pos_y):
        self.setvar('status-position', f'Cursor: ({pos_x},{pos_y})')

    def set_status(self, message=''):
        self.setvar('status-text', message)


if __name__ == '__main__':
    app = ttk.Window("ZX Editor", themename="superhero")
    ZXEditor(app)
    app.mainloop()
