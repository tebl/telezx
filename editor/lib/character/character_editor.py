import numpy, traceback, string, typing
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk
from pathlib import Path
from PIL import Image, ImageTk

from .. import BaseEditor, ZXAttribute, ZXFont, ZXGlyph, utilities, LicenseDialog, AboutDialog
from .zx_symbol_collection import ZXFontCollection, ZXGlyphCollection, ZXSymbolCollection, ZXSymbolType
from .editor_keyboard_dialog import EditorKeyboardDialog
from .symbol_type_dialog import SymbolTypeDialog

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
    
    FILE_FONT_TYPE = 'ZXFont'
    FILE_FONT_EXTENSION = '.zxfont'
    FILE_GLYPH_TYPE = 'ZXGlyph'
    FILE_GLYPH_EXTENSION = '.zxglyph'
    FILE_BINARY_TYPE = 'Binary'
    FILE_BINARY_EXTENSION = '.bin'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.attribute = ZXAttribute(ink=ZXAttribute.BLACK, paper=ZXAttribute.WHITE)
        self.scale: int=48
        self.is_debug_enabled: bool=True
        self.is_grid_enabled: bool=True

        self.document: ZXSymbolCollection = ZXFontCollection()
        self._current_offset: int=0

        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.menu = Menu(self, char_editor=self)
        self.menu.grid(row=0, column=0, columnspan=4, sticky=EW)
        self.selector = Selector(self, char_editor=self)
        self.selector.grid(row=1, column=0, rowspan=2, sticky=NSEW, padx=(10, 10), pady=(10, 10))
        self.sidebar = Sidebar(self, char_editor=self)
        self.sidebar.grid(row=1, column=3, sticky=NE, padx=(10, 10), pady=(10, 10))
        self.editor = EditingArea(self, char_editor=self)
        self.editor.grid(row=1, column=1, sticky=NW)
        self.status = Status(self, char_editor=self) 
        self.status.grid(row=3, column=0, columnspan=4, sticky=EW)

        self.master.bind("<Control-KeyPress-g>", self.on_toggle_grid)
        self.master.bind("<Control-KeyPress-n>", self.on_new)
        self.master.bind("<Control-KeyPress-o>", self.on_open)
        self.master.bind("<Control-KeyPress-s>", self.on_save)
        self.master.bind("<Control-KeyPress-q>", self.on_quit)
        self.master.bind("<Control-KeyPress-z>", self.on_undo)

        self.update_title_periodic()

    def _load_assets(self):
        return super()._load_assets({
            'new-project': 'zx-new.png',
            'open-project': 'zx-open.png',
            'save-project': 'zx-save.png',
            'set-scale': 'zx-scale.png',
            'grid-enabled': 'zx-grid.png',
            'grid-disabled': 'zx-grid-disabled.png',
            'import': 'zx-import.png',
            'export': 'zx-export.png',
            'about': 'zx-about.png',
            'logo': 'zx-logo.png',
            'function-invert': 'function-invert.png',
            'function-revert': 'function-revert.png',
            'function-clear': 'function-clear.png',
            'function-flip': 'function-flip.png',
            'function-mirror': 'function-mirror.png',
            'function-undo': 'function-undo.png',
            'function-shift-left': 'function-shift-left.png',
            'function-shift-right': 'function-shift-right.png',
            'function-shift-up': 'function-shift-up.png',
            'function-shift-down': 'function-shift-down.png'
        })

    def _get_title(self):
        return self.document.get_title()

    def on_delete_window(self, root):
        return super().on_delete_window(root)

    def on_export(self, event=None):
        try:
            filename = filedialog.asksaveasfilename(parent=self, 
                                                    title='Export project', 
                                                    filetypes=[
                                                        (self.FILE_BINARY_TYPE, (f'*{self.FILE_BINARY_EXTENSION}')),
                                                        ("All files", "*.*")], 
                                                        defaultextension=self.FILE_BINARY_EXTENSION, 
                                                        confirmoverwrite=True)
            if not filename:
                return
            self.document.export_bin(file_path=filename)
        except Exception as e:
            Messagebox.show_error(parent=self, title='Failed to select file', message=f'Failed with error:\n{e}')
            return 'break'


    def on_function_clear(self, event=None):
        self.editor.on_function_clear(event)

    def on_function_flip(self, event=None):
        self.editor.on_function_flip(event)

    def on_function_invert(self, event=None):
        self.editor.on_function_invert(event)

    def on_function_mirror(self, event=None):
        self.editor.on_function_mirror(event)

    def on_function_revert(self, event=None):
        self.document.revert_offset(self.current_offset)
        self.notify_offset_changed()

    def on_function_revert_enabled(self) -> bool:
        return self.document.can_revert_offset(self.current_offset)

    def on_function_rotate_left(self, event=None):
        self.editor.on_function_rotate_left(event)

    def on_function_rotate_right(self, event=None):
        self.editor.on_function_rotate_right(event)

    def on_function_rotate_up(self, event=None):
        self.editor.on_function_rotate_up(event)

    def on_function_rotate_down(self, event=None):
        self.editor.on_function_rotate_down(event)

    def on_function_undo(self, event=None):
        return self.on_undo(event)

    def on_function_undo_enabled(self) -> bool:
        return self.document.can_undo_offset(self.current_offset)

    def on_new(self, event=None):
        result = SymbolTypeDialog.get_result(self, 
                                             title='Select project type', 
                                             selected=self.document.__class__.__name__, 
                                             confirm_discard=self.document.has_changes())
        if result is not None:
            self.document = ZXSymbolCollection.create_from_str(symbol_type=result)
            self._current_offset = 0
            self.notify_document_changed()

    def on_import(self, symbol_type: ZXSymbolType):
        if self.document.has_changes() and not self._allow_discard('Document unsaved') == 'OK':
            return
        try:
            filename = filedialog.askopenfilename(parent=self, 
                                                  title='Import character set', 
                                                  filetypes=[
                                                      (self.FILE_BINARY_TYPE, (f'*{self.FILE_BINARY_EXTENSION}')), 
                                                      ("All files", "*.*")], 
                                                      multiple=False)
            if filename:
                self.document = ZXSymbolCollection.from_binary(filename, symbol_type)
                self.notify_document_changed()
                self.set_status(f'Symbols loaded from {filename}')
        except Exception as e:
            traceback.print_exc()
            Messagebox.show_error(parent=self, title='Load failed', message=f'Failed with error:\n{e}')
            self.set_error(f'Load error: {e}')
            print(e)
        return 'break'

    def on_import_font(self):
        self.on_import(ZXSymbolType.FONT)
        return 'break'

    def on_import_glyphs(self):
        self.on_import(ZXSymbolType.GLYPH)
        return 'break'

    def on_open(self, event=None):
        try:
            filename = filedialog.askopenfilename(parent=self, 
                                                  title='Open project', 
                                                  filetypes=[
                                                      ('TeleZX', (f'*{self.FILE_FONT_EXTENSION} *{self.FILE_GLYPH_EXTENSION}')), 
                                                      (self.FILE_FONT_TYPE, (f'*{self.FILE_FONT_EXTENSION}')), 
                                                      (self.FILE_GLYPH_TYPE, (f'*{self.FILE_GLYPH_EXTENSION}')), 
                                                      ("All files", "*.*")], 
                                                  multiple=False)
            if filename:
                if not self.document.has_changes() or self._allow_discard('Document unsaved') == 'OK':
                    self.document = self.__open_document(filename)
                    self._current_offset = self.document.constrain_offset(self._current_offset)
                    self.notify_document_changed()
                    self.set_status(f'Document loaded: {self.document.document_path}')
        except Exception as e:
            traceback.print_exc()
            Messagebox.show_error(parent=self, title='Load failed', message=f'Failed with error:\n{e}')
            self.set_error(f'Load error: {e}')
            print(e)
        return 'break'

    def __open_document(self, filename) -> ZXSymbolCollection:
        return ZXSymbolCollection.get_implementation_for(filename).from_file(filename)

    def on_open_about(self, event=None):
        AboutDialog(self).show()
        return 'break'

    def on_open_license(self, event=None):
        LicenseDialog(self).show()
        return 'break'

    def on_open_keyboard(self, event=None):
        EditorKeyboardDialog(self).show()
        return 'break'

    def on_save(self, event=None):
        if self.document.is_untitled():
            try:
                description, extension = self.__get_dialog_filetypes()
                filename = filedialog.asksaveasfilename(parent=self, 
                                                        title='Save project', 
                                                        filetypes=[
                                                            (description, (f'*{extension}')),
                                                            ("All files", "*.*")], 
                                                            defaultextension=extension, 
                                                            confirmoverwrite=True)
                if not filename:
                    return
                self.document.document_path = filename
            except Exception as e:
                Messagebox.show_error(parent=self, title='Failed to select file', message=f'Failed with error:\n{e}')
                return 'break'
        self.document.save()
        self.set_status(f'Document saved: {self.document.document_path}')
        return 'break'

    def __get_dialog_filetypes(self) -> tuple[str, str]:
        if self.document.is_type(ZXSymbolType.GLYPH):
            return (self.FILE_GLYPH_TYPE, self.FILE_GLYPH_EXTENSION)
        return (self.FILE_FONT_TYPE, self.FILE_FONT_EXTENSION)

    def on_toggle_grid(self, event=None):
        self.toggle_grid()
        return 'break'

    def on_quit(self, event=None):
        if not self.document.has_changes() or self._allow_discard('Document unsaved') == 'OK':
            self.on_delete_window(self.master)
        return 'break'

    def on_undo(self, event=None):
        self.document.undo_offset(self.current_offset)
        self.notify_offset_changed()
        return 'break'

    def notify_document_changed(self):
        self.sidebar.notify_document_changed()
        self.selector.notify_document_changed()
        self.editor.notify_document_changed()

    def notify_grid_changed(self):
        self.menu.notify_grid_changed()
        self.editor.notify_grid_changed()

    def notify_offset_changed(self):
        self.sidebar.notify_offset_changed()
        self.editor.notify_offset_changed()

    def notify_scale_changed(self):
        self.editor.notify_scale_changed()

    def notify_state_changed(self):
        '''
        Called when information has been changed, mostly used in order to
        update UI-element state for menus etc.
        '''
        self.sidebar.notify_state_changed()

    def set_scale(self, value: int):
        self.scale = value
        self.notify_scale_changed()

    def set_error(self, message):
        self.set_status(message)

    def set_status(self, message):
        self.status.set_status(message)

    @property
    def current_offset(self) -> int:
        return self._current_offset

    @current_offset.setter
    def current_offset(self, value: int):
        if not self._current_offset == value:
            self.sync_offset(self.editor.to_data(), create_undo=True)
        self._current_offset = value
        self.notify_offset_changed()

    def sync_offset(self, data, create_undo=False):
        self.document.update_offset(self._current_offset, data, create_undo)
        if create_undo:
            self.notify_state_changed()

    def toggle_grid(self):
        self.is_grid_enabled = not self.is_grid_enabled
        self.notify_grid_changed()


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
        self.notify_scale_changed()

    def __create(self):
        colour = self.__get_fill_colour()
        self.pixel_data = numpy.full(shape=(self.__get_canvas_height(), self.__get_canvas_width(), 3), fill_value=colour, dtype=numpy.uint8)

    def from_data(self, character_data):
        if type(character_data) is list:
            character_data = numpy.array(character_data, dtype=numpy.uint8), 
        self.char_data = numpy.unpackbits(character_data).reshape(8,8)

    def to_data(self):
        return numpy.packbits(self.char_data)

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
        if self.char_editor.current_offset is None:
            self.__clear()
        else:
            self.notify_offset_changed()

    def __clear(self):
        self.char_data[:] = 0
        self.refresh()

    def notify_offset_changed(self):
        try:
            char = self.char_editor.document.get_offset(self.char_editor.current_offset)
            self.from_data(char.data)
        except ValueError:
            self.char_editor.status.set_status('Invalid offset!')
            self.__clear()
        self.refresh()

    def notify_grid_changed(self):
        self.__create()
        self.refresh()

    def notify_scale_changed(self):
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

    def on_function_clear(self, event=None):
        self.char_data[:] = 0
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_invert(self, event=None):
        self.char_data = numpy.logical_not(self.char_data).astype(int)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_flip(self, event=None):
        self.char_data = numpy.flip(self.char_data, axis=0)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_mirror(self, event=None):
        self.char_data = numpy.flip(self.char_data, axis=1)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_rotate_up(self, event=None):
        self.char_data = numpy.roll(self.char_data, -1, 0)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_rotate_down(self, event=None):
        self.char_data = numpy.roll(self.char_data, 1, 0)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_rotate_left(self, event=None):
        self.char_data = numpy.roll(self.char_data, -1, 1)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
        self.refresh()

    def on_function_rotate_right(self, event=None):
        self.char_data = numpy.roll(self.char_data, 1, 1)
        self.char_editor.sync_offset(self.to_data(), create_undo=True)
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

        ## Import
        import_options = ttk.Menu(self)
        import_options.add_command(label="Font", command=self.char_editor.on_import_font)
        import_options.add_command(label="Glyphs", command=self.char_editor.on_import_glyphs)
        btn = ttk.Menubutton(
            master=self,
            text="Import",
            image='import',
            compound=LEFT,
            menu=import_options
        )
        btn.grid(row=0, column=self.__next_column())        

        ## Export
        btn = ttk.Button(
            master=self,
            text='Export',
            image='export', 
            compound=LEFT, 
            command=self.char_editor.on_export
        )
        btn.grid(row=0, column=self.__next_column())

        ## Configure scale
        self.scale_variable = ttk.IntVar()
        scale_options = ttk.Menu(self)
        for scale_up in [16, 32, 48, 64, 96, 128]:
            scale_options.add_radiobutton(
                label=f"{scale_up}x", 
                command=lambda scale_up=scale_up: self.char_editor.set_scale(scale_up), 
                variable=self.scale_variable, 
                value=scale_up)
        self.scale_variable.set(self.char_editor.scale)
        self.scale = ttk.Menubutton(
            master=self,
            text="Set scale",
            image='set-scale',
            compound=LEFT,
            menu=scale_options
        )
        self.scale.grid(row=0, column=self.__next_column())

        ## Enable display grid
        self.button_grid = ttk.Button(
            master=self, 
            text='Grid', 
            image='grid-enabled' if self.char_editor.is_grid_enabled else 'grid-disabled', 
            compound=LEFT, 
            command=self.char_editor.toggle_grid
        )
        self.button_grid.grid(row=0, column=self.__next_column())

        ## About
        about_options = ttk.Menu(self)
        about_options.add_command(label="About", command=self.char_editor.on_open_about)
        about_options.add_command(label="License", command=self.char_editor.on_open_license)
        about_options.add_separator()
        about_options.add_command(label="Keyboard", command=self.char_editor.on_open_keyboard)
        btn = ttk.Menubutton(
            master=self,
            text="About",
            image='about',
            compound=LEFT,
            menu=about_options
        )
        btn.grid(row=0, column=self.__next_column())        

    def __next_column(self) -> int:
        if self.__next_id is None:
            self.__next_id = 0
        else:
            self.__next_id += 1
        return self.__next_id

    def notify_grid_changed(self):
        img_name = 'grid-enabled' if self.char_editor.is_grid_enabled else 'grid-disabled'
        self.button_grid.config(image=img_name)


class Selector(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='info')
        self.char_editor = char_editor
        self.view = ttk.Treeview(self, columns=('Offset', 'CharCode', 'ASCII'), show='tree')
        self.view.heading('Offset', text="Offset")
        self.view.heading('CharCode', text="Character")
        self.view.heading('ASCII', text="ASCII")
        self.view.column('#0', width=90, anchor=W, stretch=False)
        self.view.column('Offset', width=50, anchor=E, stretch=False)
        self.view.column('CharCode', width=50, anchor=E, stretch=False)
        self.view.column('ASCII', width=50, anchor=CENTER, stretch=False)
        self.view.pack(side=LEFT, fill=Y, expand=True)

        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.view.yview, style='primary')
        self.scroll.pack(side=RIGHT, fill=Y)
        self.view.configure(yscrollcommand=self.scroll.set)

        self.view.bind("<Button-1>", self.on_click)
        self.view.bind("<<TreeviewSelect>>", self.on_navigation)
        # self.view.bind("<Double-Button-1>", self.on_click)

        # trigger load
        self.notify_document_changed()

    def clear(self):
        for id in self.view.get_children():
            self.view.delete(id)

    def notify_document_changed(self):
        self.clear()
        if self.char_editor.document.is_type(ZXSymbolType.FONT):
            root = self.view.insert('', 'end', text=self.char_editor.document.get_type_description(), open=True)
            alpha = self.view.insert('', 'end', text='Letters', open=True)
            numeric = self.view.insert('', 'end', text='Numbers', open=True)
            if self.char_editor.document.symbols:
                for offset, char_code, symbol in self.char_editor.document.get_symbols():
                    ascii = ZXFont.get_comparable_ascii(char_code)
                    parent = root
                    if ascii in string.ascii_letters:
                        parent = alpha
                    elif ascii in string.digits:
                        parent = numeric
                    string.ascii_letters
                    self.view.insert(parent, "end", values=(offset, char_code, ascii))
        elif self.char_editor.document.is_type(ZXSymbolType.GLYPH):
            root = self.view.insert('', 'end', text=self.char_editor.document.get_type_description(), open=True)
            ext = self.view.insert('', 'end', text='Extended', open=True)
            udg = self.view.insert('', 'end', text='UDG', open=False)
            if self.char_editor.document.symbols:
                for offset, char_code, symbol in self.char_editor.document.get_symbols():
                    parent = root
                    if char_code >= ZXGlyph.GLYPH_OFFSET_UDG:
                        parent = udg
                    elif char_code >= ZXGlyph.GLYPH_OFFSET_EXT:
                        parent = ext
                    self.view.insert(parent, "end", values=(offset, char_code, ''))
        else:
            raise ValueError('Unknown document type')

    def on_click(self, event=None):
        row = self.view.identify_row(event.y)
        self.__selection_changed(from_object=row)

    def on_navigation(self, event=None):
        focus = self.view.focus()
        self.__selection_changed(from_object=focus)

    def __selection_changed(self, from_object) -> int|None:
        if not from_object:
            return None
        item = self.view.item(from_object)
        if not item:
            return None
        values = item['values']
        if values == '':
            return None
        self.char_editor.current_offset = values[0]


type SidebarFunction = typing.Callable[[], None]
type SidebarFunctionCheck = typing.Callable[[], bool]

class Sidebar(ttk.Frame):
    char_editor: CharacterEditor

    def __init__(self, master, char_editor: CharacterEditor):
        super().__init__(master, style='dark', padding=(4, 4), borderwidth=1, relief='flat')
        self.char_editor = char_editor
        self.section_padding = (4,4)
        self.__next_row = 0
        self.__create_details()
        self.__create_functions()

    def __create_details(self):
        self.details = ttk.Frame(self, padding=(10, 10))
        self.details.grid(row=0, column=0, sticky=EW)
        self.details.columnconfigure(1, weight=1)

        self.doc_type = ttk.Label(self.details, text='Definition type:', padding=self.section_padding, style='info')
        self.doc_type.grid(row=0, column=0, sticky=W)
        self.doc_type_value = ttk.Label(self.details, text=self.char_editor.document.get_type_description(), padding=self.section_padding)
        self.doc_type_value.grid(row=0, column=1, sticky=EW)
        
        self.doc_offset = ttk.Label(self.details, text='Base offset:', padding=self.section_padding, style='info')
        self.doc_offset.grid(row=1, column=0, sticky=W)
        self.doc_offset_value = ttk.Label(self.details, text=self.char_editor.document.char_code_offset, padding=self.section_padding)
        self.doc_offset_value.grid(row=1, column=1, sticky=EW)

        self.doc_selected = ttk.Label(self.details, text='Selected:', padding=self.section_padding, style='info')
        self.doc_selected.grid(row=3, column=0, sticky=W)
        self.doc_selected_value = ttk.Label(self.details, text=self.char_editor.current_offset, padding=self.section_padding)
        self.doc_selected_value.grid(row=3, column=1, sticky=EW)

    def __create_functions(self):
        self.functions = ttk.Frame(self, padding=(0, 0))
        self.functions.grid(row=1, column=0, sticky=EW)

        self.function_checks: list[tuple[ttk.Button, SidebarFunctionCheck]] = []
        self.__create_button('Undo', 'function-undo', self.char_editor.on_function_undo, row=self.__next_row, column=0, check_func=self.char_editor.on_function_undo_enabled)
        self.__create_button('Revert', 'function-revert', self.char_editor.on_function_revert, row=self.__next_row, column=1, check_func=self.char_editor.on_function_revert_enabled)
        self.__next_row += 1
        self.__create_button('Clear', 'function-clear', self.char_editor.on_function_clear, row=self.__next_row, column=0)
        self.__create_button('Invert', 'function-invert', self.char_editor.on_function_invert, row=self.__next_row, column=1)
        self.__next_row += 1
        self.__create_button('Flip', 'function-flip', self.char_editor.on_function_flip, row=self.__next_row, column=0)
        self.__create_button('Mirror', 'function-mirror', self.char_editor.on_function_mirror, row=self.__next_row, column=1)
        self.__next_row += 1
        self.__create_button('Shift Up', 'function-shift-up', self.char_editor.on_function_rotate_up, row=self.__next_row, column=0)
        self.__create_button('Shift Down', 'function-shift-down', self.char_editor.on_function_rotate_down, row=self.__next_row, column=1)
        self.__next_row += 1
        self.__create_button('Shift Left', 'function-shift-left', self.char_editor.on_function_rotate_left, row=self.__next_row, column=0)
        self.__create_button('Shift Right', 'function-shift-right', self.char_editor.on_function_rotate_right, row=self.__next_row, column=1)
        self.__check_buttons()

    def __create_button(self, text: str, image: str, func: SidebarFunction, row, column=0, style=None, check_func: SidebarFunctionCheck|None=None):
        btn = ttk.Button(
            master=self.functions, 
            text=text,
            image=image, 
            compound=LEFT,
            style='danger link' if not style else style,
            padding=0,
            command=func,
            state='normal'
        )
        btn.grid(row=row, column=column, sticky=W, padx=10)
        if check_func:
            self.function_checks.append((btn, check_func))

    def __check_buttons(self):
        for button, check_func in self.function_checks:
            button.configure(state='normal' if check_func() else 'disable')

    def notify_document_changed(self):
        self.doc_type_value.configure(text=self.char_editor.document.get_type_description())
        self.doc_offset_value.configure(text=self.char_editor.document.char_code_offset)
        self.notify_offset_changed()

    def notify_offset_changed(self):
        self.doc_selected_value.configure(text=self.char_editor.current_offset)
        self.__check_buttons()

    def notify_state_changed(self):
        self.__check_buttons()


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