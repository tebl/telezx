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

from .. import BaseEditor, ZXAttributeRGB, ZXScreen, ZXFont, ZXGlyph, ZXToken, utilities
from .zx_font_definition import ZXFontDefinition

class CharacterEditor(BaseEditor):
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
    
    FILE_TYPE = 'ZXFont'
    FILE_EXTENSION = '.zxfont'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.attribute = ZXAttributeRGB(ink=ZXAttributeRGB.BLACK, paper=ZXAttributeRGB.WHITE)
        self.scale: int=48
        self.is_debug_enabled: bool=True
        self.is_grid_enabled: bool=True

        self.document = ZXFontDefinition()
        self._current_offset: int=0

        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.menu = Menu(self, char_editor=self)
        self.menu.grid(row=0, column=0, columnspan=4, sticky=EW)
        self.selector = Selector(self, char_editor=self)
        self.selector.grid(row=1, column=0, rowspan=2, sticky=NSEW, padx=(10, 10), pady=(10, 10))
        self.sidebar = Sidebar(self, char_editor=self)
        self.sidebar.grid(row=1, column=3, sticky=NSEW, padx=(10, 10), pady=(10, 10))
        self.editor = EditingArea(self, char_editor=self)
        self.editor.grid(row=1, column=1, sticky=NW)
        self.status = Status(self, char_editor=self)
        self.status.grid(row=3, column=0, columnspan=4, sticky=EW)

        self.master.bind("<Control-KeyPress-n>", self.on_new)
        self.master.bind("<Control-KeyPress-o>", self.on_open)
        self.master.bind("<Control-KeyPress-s>", self.on_save)
        self.master.bind("<Control-KeyPress-q>", self.on_quit)

        self.update_title_periodic()

    def _load_assets(self):
        return super()._load_assets({
            'new-project': 'zx-new.png',
            'open-project': 'zx-open.png',
            'save-project': 'zx-save.png',
            'set-scale': 'zx-scale.png',
            'grid-enabled': 'zx-grid.png',
            'grid-disabled': 'zx-grid-disabled.png',
            'export': 'zx-export.png',
            'about': 'zx-about.png',
            'logo': 'zx-logo.png'
        })

    def _get_title(self):
        return self.document.get_title()

    def on_delete_window(self, root):
        return super().on_delete_window(root)

    def on_new(self, event=None):
        if self.document.has_changes() and not self._allow_discard('Document unsaved') == 'OK':
            return
        self.document = ZXFontDefinition()
        self._current_offset = 0
        # self.document.import_bin(utilities.get_project_root() / 'fonts'/ 'font_default.bin')
        self.notify_document_changed()

    def on_open(self, event=None):
        try:
            filename = filedialog.askopenfilename(parent=self, title='Open project', filetypes=[(self.FILE_TYPE, (f'*{self.FILE_EXTENSION}')), ("All files", "*.*")], multiple=False)
            if filename:
                if not self.document.has_changes() or self._allow_discard('Document unsaved') == 'OK':
                    self.document = ZXFontDefinition.from_file(filename)
                    self._current_offset = self.document.constrain_offset(self._current_offset)
                    self.notify_document_changed()
                    self.set_status(f'Document loaded: {self.document.document_path}')
        except Exception as e:
            traceback.print_exc()
            Messagebox.show_error(parent=self, title='Load failed', message=f'Failed with error:\n{e}')
            self.set_error(f'Load error: {e}')
            print(e)
        return 'break'

    def on_save(self, event=None):
        if self.document.is_untitled():
            try:
                filename = filedialog.asksaveasfilename(parent=self, title='Save project', filetypes=[(self.FILE_TYPE, (f'*{self.FILE_EXTENSION}')), ("All files", "*.*")], defaultextension=self.FILE_EXTENSION, confirmoverwrite=True)
                if not filename:
                    return
                self.document.document_path = filename
            except Exception as e:
                Messagebox.show_error(parent=self, title='Failed to select file', message=f'Failed with error:\n{e}')
                return 'break'
        self.document.save()
        self.set_status(f'Document saved: {self.document.document_path}')
        return 'break'

    def on_quit(self, event=None):
        self.on_delete_window(self.master)
        return 'break'

    def notify_document_changed(self):
        self.sidebar.notify_document_changed()
        self.selector.notify_document_changed()
        self.editor.notify_document_changed()

    def notify_offset_changed(self):
        self.sidebar.notify_offset_changed()
        self.editor.notify_offset_changed()

    def set_offset(self, value: int):
        self._current_offset = value
        self.notify_offset_changed()

    def set_status(self, message):
        self.status.set_status(message)

    def get_current_offset(self) -> int:
        return self._current_offset

    def sync_offset(self, data):
        self.document.update_offset(self._current_offset, data)

class EditingArea(ttk.Frame):
    NOGRID_Y_OFFSET = 2

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master)
        self.char_editor = char_editor

        self.default_fill = colorutils.color_to_rgb(master.master.style.colors.get('bg'))
        self.grid_colour = colorutils.color_to_rgb(master.master.style.colors.get('dark'))

        self.char_data = numpy.zeros(shape=(8,8), dtype=numpy.uint8)

        self.label = ttk.Label(self)
        self.label.pack(padx=5, pady=5)

        self.label.bind('<B1-Motion>', self.on_click)
        self.label.bind('<Button-1>', self.on_click)
        self.label.bind('<Button-3>', self.on_click_alt)
        self.label.bind('<B3-Motion>', self.on_click_alt)
        self.notify_scale_changed(self.char_editor.scale)

    def __create(self):
        colour = self.__get_fill_colour()
        self.pixel_data = numpy.full(shape=(self.__get_canvas_height(), self.__get_canvas_width(), 3), fill_value=colour, dtype=numpy.uint8)

    def from_data(self, character_data):
        for pos_y, packed in enumerate(character_data):
            self.char_data[pos_y:] = numpy.unpackbits(packed)

    def to_data(self):
        return [ numpy.packbits(v)[0] for v in self.char_data ]

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

    def notify_document_changed(self):
        if self.char_editor.get_current_offset() is None:
            self.__clear()
        else:
            self.notify_offset_changed()

    def __clear(self):
        self.char_data[:] = 0
        self.refresh()

    def notify_offset_changed(self):
        try:
            char = self.char_editor.document.get_offset(self.char_editor.get_current_offset())
            self.from_data(char.data)
        except ValueError:
            self.char_editor.status.set_status('Invalid offset!')
            self.__clear()
        self.refresh()

    def notify_grid_changed(self, grid_enabled):
        self.__create()
        self.refresh()

    def notify_scale_changed(self, scale_value):
        self.__create()
        self.refresh()

    def on_click(self, event=None):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            char_x, char_y = self.get_screen_position(event.x, event.y)
            self.__update_cell(char_x, char_y, 1)

    def on_click_alt(self, event=None):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            char_x, char_y = self.get_screen_position(event.x, event.y)
            self.__update_cell(char_x, char_y, 0)

    def refresh(self):
        self.pixel_data[:] = self.__get_fill_colour()
        for char_x, char_y in self.__cell_order():
            self.__refresh_cell(char_x, char_y)
        self.__flip_canvas()

    def __cell_order(self):
        for char_x in range(8):
            for char_y in range(8):
                yield (char_x, char_y)

    def __update_cell(self, pos_x: int, pos_y: int, value: int):
        self.char_data[pos_y][pos_x] = value
        self.char_editor.sync_offset(self.to_data())
        self.__refresh_cell(pos_x, pos_y)
        self.__flip_canvas()

    def __refresh_cell(self, pos_x: int, pos_y: int):
        pix_x, pix_y, pix_size = self.get_canvas_position(pos_x, pos_y)
        self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = self.__get_rgb(pos_x, pos_y)

    def __get_rgb(self, pos_x: int, pos_y: int):
        return self.char_editor.attribute.to_rgb(self.char_data[pos_y][pos_x] == 1)

    def get_canvas_position(self, pos_x, pos_y) -> tuple[int, int, int]:
        '''
        Translate from cursor location to pixel ranges within the displayed canvas,
        adjusted for whether a 1px wide grid is enabled. If not enabled then we
        will instead try to center image within canvas.
        '''
        x = pos_x*self.char_editor.scale
        y = pos_y*self.char_editor.scale
        if self.char_editor.is_grid_enabled:
            x += pos_x + 1
            y += pos_y + 1
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
        self.view = ttk.Treeview(self, columns=('Offset', 'CharCode', 'ASCII'), show='tree')
        self.view.heading('Offset', text="Offset")
        self.view.heading('CharCode', text="Character")
        self.view.heading('ASCII', text="ASCII")
        self.view.column('#0', width=80, anchor=W, stretch=False)
        self.view.column('Offset', width=50, anchor=E, stretch=False)
        self.view.column('CharCode', width=50, anchor=E, stretch=False)
        self.view.column('ASCII', width=50, anchor=CENTER, stretch=False)
        self.view.pack(side=LEFT, fill=Y, expand=True)

        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.view.yview, style='primary')
        self.scroll.pack(side=RIGHT, fill=Y)
        self.view.configure(yscrollcommand=self.scroll.set)

        self.view.bind("<Button-1>", self.on_click)
        # self.view.bind("<Double-Button-1>", self.on_click)

        # trigger load
        self.notify_document_changed()

    def clear(self):
        for id in self.view.get_children():
            self.view.delete(id)

    def notify_document_changed(self):
        self.clear()
        if self.char_editor.document.is_font():
            self.root = self.view.insert('', 'end', text='Characters', open=True)
            if self.char_editor.document.symbols:
                for offset, char_code, symbol in self.char_editor.document.get_symbols():
                    ascii = ZXFont.get_comparable_ascii(char_code)
                    self.view.insert(self.root, "end", values=(offset, char_code, ascii))
        else:
            self.root = self.view.insert('', 'end', text='Glyphs', open=True)
            if self.char_editor.document.symbols:
                for offset, char_code, symbol in self.char_editor.document.get_symbols():
                    self.view.insert(self.root, "end", values=(offset, char_code, ''))

    def on_click(self, event=None):
        row = self.view.identify_row(event.y)
        if not row:
            return
        values = self.view.item(row)['values']
        if not values:
            return
        self.char_editor.set_offset(self.view.item(row)['values'][0])

class Sidebar(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='dark', padding=(4, 4), borderwidth=1, relief='flat')
        self.char_editor = char_editor
        self.__create_details()

    def __create_details(self):
        self.details = ttk.Frame(self)
        self.details.grid(row=0, column=0, sticky=NW)
        self.details.columnconfigure(1, weight=1)

        padding = (4,4)
        self.doc_type = ttk.Label(self.details, text='Definition type:', padding=padding, style='info')
        self.doc_type.grid(row=0, column=0, sticky=W)
        self.doc_type_value = ttk.Label(self.details, text=self.char_editor.document.get_type(), padding=padding)
        self.doc_type_value.grid(row=0, column=1, sticky=EW)
        
        self.doc_offset = ttk.Label(self.details, text='Base offset:', padding=padding, style='info')
        self.doc_offset.grid(row=1, column=0, sticky=W)
        self.doc_offset_value = ttk.Label(self.details, text=self.char_editor.document.char_code_offset, padding=padding)
        self.doc_offset_value.grid(row=1, column=1, sticky=EW)

        self.doc_selected = ttk.Label(self.details, text='Selected:', padding=padding, style='info')
        self.doc_selected.grid(row=3, column=0, sticky=W)
        self.doc_selected_value = ttk.Label(self.details, text=self.char_editor.get_current_offset(), padding=padding)
        self.doc_selected_value.grid(row=3, column=1, sticky=EW)

    def notify_document_changed(self):
        self.doc_type_value.configure(text=self.char_editor.document.get_type())
        self.doc_offset_value.configure(text=self.char_editor.document.char_code_offset)
        self.notify_offset_changed()

    def notify_offset_changed(self):
        self.doc_selected_value.configure(text=self.char_editor.get_current_offset())

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