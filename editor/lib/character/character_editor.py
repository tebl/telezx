#!python3
import numpy
import traceback
import string
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk
from pathlib import Path
from PIL import Image, ImageTk

from .. import ZXAttributeRGB, ZXScreen, ZXFont, ZXGlyph, ZXToken, utilities

class CharacterEditor(ttk.Frame):
    PROGRAM_TITLE = 'ZX Character Editor'
    PROGRAM_URL = 'https://github.com/tebl/telezx'
    PROGRAM_COPYRIGHT = "Copyright © 2026 Tor-Eirik Bakke Lunde"
    PROGRAM_LICENSE_URL = f'{PROGRAM_URL}/blob/main/LICENSE.md'
    PROGRAM_LICENSE = "This application comes with absolutely no warranty.\nSee the GNU General Public Licence, version 3 or later for details."
    PROGRAM_LICENSE_FULL = '''\
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <https://www.gnu.org/licenses/>.'''


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.__load_assets()
        self.attribute = ZXAttributeRGB(ink=ZXAttributeRGB.BLACK, paper=ZXAttributeRGB.WHITE)
        self.scale: int=48
        self.is_debug_enabled: bool=True
        self.is_grid_enabled: bool=True

        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)

        self.menu = Menu(self, char_editor=self)
        self.menu.grid(row=0, column=0, columnspan=4, sticky=EW)

        self.selector = Selector(self, char_editor=self)
        self.selector.grid(row=1, column=0, rowspan=2, sticky=NSEW)

        self.sidebar = Sidebar(self, char_editor=self)
        self.sidebar.grid(row=1, column=3, sticky=NSEW, padx=5, pady=5)

        self.editor = EditingArea(self, char_editor=self)
        self.editor.grid(row=1, column=1, sticky=NW)

        self.status = Status(self, char_editor=self)
        self.status.grid(row=3, column=0, columnspan=4, sticky=EW)
        self.status.set_status('Editor started')

    def __load_assets(self):
        image_files = {
            'new-project': 'zx-new.png',
            'open-project': 'zx-open.png',
            'save-project': 'zx-save.png',
            'set-scale': 'zx-scale.png',
            'grid-enabled': 'zx-grid.png',
            'grid-disabled': 'zx-grid-disabled.png',
            'export': 'zx-export.png',
            'about': 'zx-about.png',
            'logo': 'zx-logo.png'
        }

        self.photoimages = []        
        img_path = utilities.get_project_root() / 'assets'
        for key, val in image_files.items():
            _path = img_path / val
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))

    def on_new(self):
        pass

    def on_open(self):
        pass

    def on_save(self):
        pass

    def on_quit(self, root):
        root.destroy()


class EditingArea(ttk.Frame):
    NOGRID_Y_OFFSET = 2

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master)
        self.char_editor = char_editor

        self.default_fill = colorutils.color_to_rgb(master.master.style.colors.get('bg'))
        self.grid_colour = colorutils.color_to_rgb(master.master.style.colors.get('dark'))

        self.char_data = numpy.zeros(shape=(8,8), dtype=numpy.uint8)

        font = ZXFont.get_default()
        self.from_data(font.get_offset(1))

        self.label = ttk.Label(self)
        self.label.pack(padx=5, pady=5)
        self.label.bind('<Button-1>', self.on_click)
        # self.label.bind('<Motion>', self.on_click)
        self.label.bind('<Button-3>', self.on_click_alt)
        self.notify_scale_changed(self.char_editor.scale)

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def __create(self):
        colour = self.__get_fill_colour()
        self.pixel_data = numpy.full(shape=(self.__get_canvas_height(), self.__get_canvas_width(), 3), fill_value=colour, dtype=numpy.uint8)

    def from_data(self, character_data):
        for char_y, packed in enumerate(character_data):
            self.char_data[char_y:] = numpy.unpackbits(packed)

    def __get_fill_colour(self):
        if self.char_editor.is_grid_enabled:
            return self.grid_colour
        return self.default_fill

    def __get_canvas_width(self):
        num_pixels = 8*self.char_editor.scale
        num_pixels += 8
        return num_pixels

    def __get_canvas_height(self):
        num_pixels = 8*self.char_editor.scale
        num_pixels += 8
        return num_pixels

    def notify_grid_changed(self, grid_enabled):
        self.__create()
        self.refresh()

    def notify_scale_changed(self, scale_value):
        self.__create()
        self.refresh()

    def on_click(self, event=None):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            char_x, char_y = self.get_screen_position(event.x, event.y)
            print(event.x, event.y, '->', char_x, char_y)
        # self.refresh()

    def on_click_alt(self, event=None):
        font = ZXFont.get_default()
        self.from_data(font.get_offset(2))
        self.refresh()

    def refresh(self):
        self.pixel_data[:] = self.__get_fill_colour()
        for char_x, char_y in self.__cell_order():
            self.__refresh_cell(char_x, char_y)
        self.__flip_canvas()

    def __cell_order(self):
        for char_x in range(8):
            for char_y in range(8):
                yield (char_x, char_y)

    def __refresh_cell(self, char_x: int, char_y: int):
        pix_x, pix_y, pix_size = self.get_canvas_position(char_x, char_y)
        # rgb_x, rgb_y, rgb_size = self.__get_screen_position(char_x, char_y)
        self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = self.__get_rgb(char_x, char_y)

    def __get_rgb(self, char_x: int, char_y: int):
        return self.char_editor.attribute.to_rgb(self.char_data[char_y][char_x] == 1)

    def get_canvas_position(self, char_x, char_y) -> tuple[int, int, int]:
        '''
        Translate from cursor location to pixel ranges within the displayed canvas,
        adjusted for whether a 1px wide grid is enabled. If not enabled then we
        will instead try to center image within canvas.
        '''
        x = char_x*self.char_editor.scale
        y = char_y*self.char_editor.scale
        if self.char_editor.is_grid_enabled:
            x += char_x + 1
            y += char_y + 1
        else:
            x += 8 // 2
            y+= self.NOGRID_Y_OFFSET
        return (x, y, self.char_editor.scale)


    def get_screen_position(self, pos_x, pos_y):
        '''
        Translates a pixel location within the displayed canvas to cursor location.
        '''
        cell_size = self.char_editor.scale
        if self.char_editor.is_grid_enabled:
            char_x = ((pos_x - 1) // (cell_size + 1)) if pos_x >= 1 else 0
            char_y = ((pos_y - 1) // (cell_size + 1)) if pos_y >= 1 else 0
            return (char_x, char_y)

        char_x = ((pos_x - (8 // 2)) // cell_size)
        if char_x < 0 or char_x >= 8:
            char_x = -1

        char_y = ((pos_y - self.NOGRID_Y_OFFSET) // cell_size)
        if char_y < 0 or char_y >= 8:
            char_y = -1
        return (char_x, char_y)


    def __flip_canvas(self):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img


class Menu(ttk.Frame):
    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='primary.TFrame')
        self.char_editor = char_editor
        self.__next_id: int|None = None

        ## New...
        btn = ttk.Button(
            master=self,
            text='New...',
            image='new-project', 
            compound=LEFT, 
            command=self.char_editor.on_new
        )
        btn.grid(row=0, column=self.__next_column())

        ## Open...
        btn = ttk.Button(
            master=self,
            text='Open',
            image='open-project', 
            compound=LEFT, 
            command=self.char_editor.on_open
        )
        btn.grid(row=0, column=self.__next_column())

        ## Save
        btn = ttk.Button(
            master=self,
            text='Save',
            image='save-project', 
            compound=LEFT, 
            command=self.char_editor.on_save
        )
        btn.grid(row=0, column=self.__next_column())

    # def notify_grid_changed(self, value):
    #     img_name = 'grid-disabled' if value else 'grid-enabled'
    #     self.button_grid.config(image=img_name)

    def __next_column(self) -> int:
        if self.__next_id is None:
            self.__next_id = 0
        else:
            self.__next_id += 1
        return self.__next_id


class Selector(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='info')
        self.char_editor = char_editor
        self.view = ttk.Treeview(self, columns=('offset', 'character'), show='tree')
        self.view.heading('offset', text="Offset")
        self.view.heading('character', text="Character")
        self.view.column('#0', width=100, anchor=W, stretch=False)
        self.view.column('offset', width=50, anchor=W, stretch=False)
        self.view.column('character', width=50, anchor=W, stretch=False)
        self.view.pack(fill=Y, expand=True)

        font = ZXFont.get_default()
        root = self.view.insert('', 'end', text='Symbols', open=True)
        for char_code, data in font.symbols():
            char = chr(char_code)
            self.view.insert(root, "end", values=(char_code, char if char in string.printable else ''))


class Sidebar(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='dark', padding=(4, 4))
        self.char_editor = char_editor

        lbl_1 = ttk.Label(self, text='Test1')
        lbl_1.pack()

        lbl_2 = ttk.Label(self, text='Test2')
        lbl_2.pack()

        lbl_3 = ttk.Label(self, text='Test3')
        lbl_3.pack()

        # lbl = ttk.Label(self, text="Ink:")
        # lbl.grid(row=0, column=0, sticky=W, padx=(0, 4))
        # self.ink_widgets = []


class Status(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='dark.TFrame')
        self.char_editor = char_editor
        self.columnconfigure(1, weight=1)

        self.status = ttk.Label(
            master=self,
            textvariable='status-text',
            bootstyle="inverse-dark"
        )
        self.status.grid(row=0, column=0)
        self.set_status('')

        self.position = ttk.Label(
            master=self,
            textvariable='status-position',
            bootstyle="inverse-dark"
        )
        self.position.grid(row=0, column=2)

    def set_status(self, message=''):
        self.setvar('status-text', message)