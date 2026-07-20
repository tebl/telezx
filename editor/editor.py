import numpy
import traceback
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk
from pathlib import Path
from PIL import Image, ImageTk

from lib import ZXScreen, ZXFont, ZXGlyph, ZXDocument


class ZXEditor(ttk.Frame):
    PROGRAM_TITLE = 'ZX Editor'
    SCALE_MAX = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.__load_assets()

        self.scale = 3
        self.is_grid_enabled = True
        self.is_sticky_enabled = False
        self.is_overwrite_enabled = False
        self.cursor_x = 0
        self.cursor_y = 0

        self.zx_document = ZXDocument()
        self.copied_format = None

        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)

        self.menu = Menu(self, zx_editor=self)
        self.menu.grid(row=0, column=0, columnspan=3, sticky=EW)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=1, column=1, sticky=NE)

        self.main = Main(self)
        self.main.grid(row=1, column=0, sticky=NW)

        self.status = Status(self, zx_editor=self)
        self.status.grid(row=3, column=0, columnspan=3, sticky=EW)

        self.__load_font()
        self.__load_glyph()

        self.master.bind("<Control-KeyPress-n>", self.clicked_new)
        self.master.bind("<Control-KeyPress-o>", self.clicked_open)
        self.master.bind("<Control-KeyPress-s>", self.clicked_save)
        self.master.bind("<Control-KeyPress-b>", self.clicked_background)
        self.master.bind("<Control-KeyPress-g>", self.clicked_grid)
        self.master.bind("<Control-KeyPress-z>", self.move_cursor_left)
        self.master.bind("<Control-KeyPress-f>", self.clicked_toggle_sticky)
        self.master.bind("<Control-KeyPress-q>", self.clicked_quit)
        self.master.bind("<Control-KeyPress-i>", self.clicked_invert)
        self.master.bind("<Control-KeyPress-C>", self.clicked_copy_attribute)
        self.master.bind("<Control-KeyPress-V>", self.clicked_paste_attribute)
        self.master.bind("<Key>", self.keyboard_event)

        self.update_title_periodic()

    def clicked_background(self, event=None):
        try:
            filename = filedialog.askopenfilename(parent=self, title='Set background', filetypes=[("SCR", ('*.scr')), ("All files", "*.*")], multiple=False)
            if filename:
                self.zx_document.set_background(filename)
                self.refresh()
                self.set_status(f'Background loaded: {filename}')
        except Exception as e:
            Messagebox.show_error(parent=self, title='Failed to open file', message=f'Failed with error:\n{e}')
        return 'break'

    def clicked_grid(self, event=None):
        self.is_grid_enabled = (not self.is_grid_enabled)
        self.main.notify_grid_changed(self.is_grid_enabled)
        self.menu.notify_grid_changed(self.is_grid_enabled)
        if event is not None:
            self.main.focus_set()
        return 'break'

    def clicked_save_screenshot(self, event=None):
        try:
            filetypes = [
                ("PNG", ('*.png')),
                ("BMP", ('*.bmp')), 
                ("JPG", ('*.jpg')), 
                ("PPM", ('*.ppm')), 
                ("All images", "*.bmp *.jpg *.png")
            ]
            filename = filedialog.asksaveasfilename(parent=self, title='Save screenshot', filetypes=filetypes, defaultextension='.png', confirmoverwrite=True)
            if filename:
                self.zx_document.export_screenshot(filename)
                self.set_status(f'Exported screenshot: {filename}')
        except Exception as e:
            Messagebox.show_error(parent=self, title='Export failed', message=f'Failed with error:\n{e}')
            self.set_status(f'{e}')

    def clicked_export_scr(self, event=None):
        try:
            filename = filedialog.asksaveasfilename(parent=self, title='Export to SCR', filetypes=[("SCR", ('*.scr')), ("All files", "*.*")], defaultextension='.scr', confirmoverwrite=True)
            if filename:
                self.zx_document.export_to_scr(scr_path=filename)
                self.set_status(f'Exported SCR: {filename}')
        except Exception as e:
            Messagebox.show_error(parent=self, title='Export failed', message=f'Failed with error:\n{e}')
            self.set_status(f'{e}')
        return 'break'

    def clicked_export_specscii(self, event=None):
        try:
            filename = filedialog.asksaveasfilename(parent=self, title='Export to SPECSCII', filetypes=[("TeleZX Token", ('*.tkn')), ("SPECSCII", ('*.specscii')), ("All files", "*.*")], defaultextension='.tkn', confirmoverwrite=True)
            if filename:
                self.zx_document.export_to_specscii(specscii_path=filename)
                self.set_status(f'Exported SPECSCII: {filename}')
        except Exception as e:
            traceback.print_exc()
            Messagebox.show_error(parent=self, title='Export failed', message=f'Failed with error:\n{e}')
            self.set_status(f'{e}')
        return 'break'

    def clicked_invert(self, event=None):
        prev_sticky = self.is_sticky_enabled
        is_inverted = (self.sidebar.palette.get_inverted() == ZXDocument.UNDEFINED)
        self.sidebar.palette.changed_inverted(is_inverted)
        self.set_sticky(prev_sticky)
        if event is not None:
            self.main.focus_set()
        return 'break'

    def clicked_new(self, event=None):
        if self.zx_document.has_changes():
            if not self.__allow_discard('Document unsaved') == 'OK':
                return
        self.zx_document.clear(ZXDocument.DEFAULT_ATTRIBUTE)
        self.__load_font()
        self.__load_glyph()
        self.refresh()
        self.set_status('New untitled document')
        self.update_title()
        return 'break'

    def __allow_discard(self, title):
        return Messagebox.okcancel(parent=self, title=title, message='Document has unsaved changes, do you want to discard these?')

    def clicked_open(self, event=None):
        try:
            filename = filedialog.askopenfilename(parent=self, title='Open project', filetypes=[("TeleZX", ('*.telezx')), ("All files", "*.*")], multiple=False)
            if filename:
                if not self.zx_document.has_changes() or self.__allow_discard('Document unsaved') == 'OK':
                    self.zx_document.load(filename)
                    self.__load_font()
                    self.__load_glyph()
            self.set_status(f'Document loaded: {self.zx_document.document_path}')
        except Exception as e:
            traceback.print_exc()
            Messagebox.show_error(parent=self, title='Load failed', message=f'Failed with error:\n{e}')
            self.set_status(f'Load error: {e}')
            print(e)
        self.refresh()
        return 'break'

    def __load_font(self):
        self.sidebar.symbols.notify_font_changed(self.zx_document.font_path)

    def __load_glyph(self):
        self.sidebar.symbols.notify_glyph_changed(self.zx_document.glyph_path)

    def clicked_save(self, event=None):
        if self.zx_document.is_blank():
            try:
                filename = filedialog.asksaveasfilename(parent=self, title='Save project', filetypes=[("TeleZX", ('*.telezx')), ("All files", "*.*")], defaultextension='.telezx', confirmoverwrite=True)
                if not filename:
                    return
                self.zx_document.set_document(filename)
            except Exception as e:
                Messagebox.show_error(parent=self, title='Failed to select file', message=f'Failed with error:\n{e}')
        self.zx_document.save()
        self.set_status(f'Document saved: {self.zx_document.document_path}')
        return 'break'

    def clicked_copy_attribute(self, event=None):
        self.copied_format = self.sidebar.palette.get_dataset()
        self.set_status(f"Copied {self.copied_format}")

    def clicked_paste_attribute(self, event=None):
        if not self.zx_document.is_defined(self.cursor_x, self.cursor_y):
            self.set_status("Character cell is UNDEFINED")
            return
        if not self.copied_format:
            self.set_status('Copy attribute data first')
            return
        
        changed = self.zx_document.set_attribute(self.cursor_x, self.cursor_y, self.copied_format.attribute)
        if self.zx_document.set_inverted(self.cursor_x, self.cursor_y, self.copied_format.is_inverted):
            changed = True
        if changed:
            self.move_cursor(self.cursor_x, self.cursor_y)
        self.set_status(f"Pasted {self.copied_format}")
        return 'break'
        
    def clicked_toggle_sticky(self, event=None):
        self.set_sticky(not self.is_sticky_enabled)
        if event is not None:
            self.main.focus_set()
        return 'break'

    def clicked_quit(self, event=None):
        self.on_quit(self.master)
        return 'break'

    def keyboard_event(self, event):
        if self.main.check_focus():
            self.main.focus_set()
            match event.keysym:
                case 'Enter' | 'KP_Enter' | 'Return':
                    self.move_cursor_newline()
                case 'Home' | 'KP_Home':
                    if self.cursor_x == 0:
                        self.move_cursor(0, 0)
                        return
                    self.move_cursor(0, self.cursor_y)
                case 'End' | 'KP_End':
                    if self.cursor_x == (ZXScreen.SCREEN_WIDTH_CHARS - 1):
                        self.move_cursor(
                            ZXScreen.SCREEN_WIDTH_CHARS - 1, 
                            ZXScreen.SCREEN_HEIGHT_CHARS - 1)
                        return
                    self.move_cursor(
                        ZXScreen.SCREEN_WIDTH_CHARS - 1, 
                        self.cursor_y)
                case 'Up' | 'KP_Up':
                    self.move_cursor_up()
                case 'Down' | 'KP_Down':
                    self.move_cursor_down()
                case 'Left' | 'KP_Left':
                    self.move_cursor_left()
                case 'Right' | 'KP_Right':
                    self.move_cursor_right()
                case 'BackSpace':
                    char_x = self.cursor_x
                    char_y = self.cursor_y
                    if char_x > 0:
                        char_x -= 1
                    else:
                        if char_y > 0:
                            char_x = 0
                            char_y -= 1
                    self.zx_document.set_inverted(char_x, char_y, ZXDocument.UNDEFINED)
                    self.zx_document.set_character(char_x, char_y, ZXDocument.UNDEFINED)
                    self.zx_document.set_attribute(char_x, char_y, ZXDocument.UNDEFINED)
                    self.move_cursor(char_x, char_y)
                    self.refresh()
                case 'Shift_L' | 'Shift_R' | 'Control_L' | 'Control_R':
                    pass
                case 'Delete' | 'KP_Delete':
                    self.zx_document.set_inverted(self.cursor_x, self.cursor_y, ZXDocument.UNDEFINED)
                    self.zx_document.set_character(self.cursor_x, self.cursor_y, ZXDocument.UNDEFINED)
                    self.zx_document.set_attribute(self.cursor_x, self.cursor_y, ZXDocument.UNDEFINED)
                    self.move_cursor(self.cursor_x, self.cursor_y)
                    self.refresh()
                case 'Insert' | 'KP_Insert':
                    self.set_overwrite(not self.is_overwrite_enabled)
                case _:
                    if event.char:
                        ascii_code = ord(event.char)
                        if ZXFont.validate_ascii(ascii_code):
                            self.set_cursor_character(ascii_code)
                            return
                    # print('Unknown key:', event.char, event.keysym, event.keycode)

    def move_cursor(self, char_x, char_y):
        self.cursor_x = (char_x % ZXScreen.SCREEN_WIDTH_CHARS)
        self.cursor_y = (char_y % ZXScreen.SCREEN_HEIGHT_CHARS)
        self.zx_document.debug_cell(self.cursor_x, self.cursor_y)
        self.main.notify_cursor_changed(self.cursor_x, self.cursor_y)
        self.status.notify_cursor_changed(self.cursor_x, self.cursor_y)

    def move_cursor_up(self, event=None):
        if self.cursor_y > 0:
            self.move_cursor(self.cursor_x, self.cursor_y - 1)

    def move_cursor_down(self, event=None):
        if self.cursor_y < (ZXScreen.SCREEN_HEIGHT_CHARS - 1):
            self.move_cursor(self.cursor_x, self.cursor_y + 1)

    def move_cursor_left(self, event=None):
        if self.cursor_x > 0:
            self.move_cursor(self.cursor_x - 1, self.cursor_y)
        else:
            if self.cursor_y > 0:
                self.move_cursor(ZXScreen.SCREEN_WIDTH_CHARS - 1, self.cursor_y - 1)
        return 'break'
    
    def move_cursor_right(self, event=None):
        if self.cursor_x < (ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.move_cursor(self.cursor_x + 1, self.cursor_y)
            return
        if self.cursor_y < (ZXScreen.SCREEN_HEIGHT_CHARS - 1):
            self.move_cursor(0, self.cursor_y + 1)

    def move_cursor_newline(self, event=None):
        if self.cursor_y < (ZXScreen.SCREEN_HEIGHT_CHARS - 1):
            self.move_cursor(0, self.cursor_y + 1)

    def on_quit(self, root):
        if not self.zx_document.has_changes() or self.__allow_discard('Document unsaved') == 'OK':
            root.destroy()

    def refresh(self):
        self.main.refresh()

    def set_cursor_character(self, char_code):
        changed = False
        if self.zx_document.set_character(self.cursor_x, self.cursor_y, char_code):
            changed = True
        if self.zx_document.set_attribute(
            self.cursor_x, 
            self.cursor_y, 
            self.sidebar.palette.get_attribute()):
            changed = True
        if self.zx_document.set_inverted(self.cursor_x, self.cursor_y, self.sidebar.palette.get_inverted()):
            changed = True

        if not self.is_overwrite_enabled:
            self.move_cursor_right()
        if changed:
            self.refresh()

    def set_cursor_attribute(self, attribute):
        self.set_sticky(True)
        if not self.zx_document.is_defined(self.cursor_x, self.cursor_y):
            return
        changed = self.zx_document.set_attribute(self.cursor_x, self.cursor_y, attribute)
        if changed:
            self.refresh()

    def set_cursor_inverted(self, is_inverted):
        self.set_sticky(True)
        if not self.zx_document.is_defined(self.cursor_x, self.cursor_y):
            return
        changed = self.zx_document.set_inverted(self.cursor_x, self.cursor_y, is_inverted)
        if changed:
            self.refresh()

    def set_scale(self, value):
        self.scale = value
        self.main.notify_scale_changed(value)
        # Uncomment to rescale symbols
        # self.__load_font()
        # self.__load_glyph()
        self.sidebar.palette.notify_scale_changed(value)
        self.set_status(f'Scale set to {self.scale}x')

    def set_status(self, message):
        self.status.set_status(message)

    def set_sticky(self, value):
        self.is_sticky_enabled = value
        self.sidebar.palette.notify_sticky_changed(value)

    def set_overwrite(self, value):
        self.is_overwrite_enabled = value
        self.sidebar.palette.notify_overwrite_changed(value)

    def update_title_periodic(self):
        self.update_title()
        self.after(250, self.update_title_periodic)

    def update_title(self):
        self.master.title(
            "{} ({})".format(
                self.PROGRAM_TITLE, 
                self.zx_document.get_description()
            )
        )

    def __load_assets(self):
        image_files = {
            'new-project': 'zx-new.png',
            'open-project': 'zx-open.png',
            'save-project': 'zx-save.png',
            'set-background': 'zx-background.png',
            'set-scale': 'zx-scale.png',
            'grid-enabled': 'zx-grid.png',
            'grid-disabled': 'zx-grid-disabled.png',
            'export': 'zx-export.png'
        }

        self.photoimages = []
        imgpath = Path(__file__).parent / 'assets'
        for key, val in image_files.items():
            _path = imgpath / val
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))


class Menu(ttk.Frame):
    def __init__(self, master, zx_editor: ZXEditor):
        super().__init__(master, style='primary.TFrame')
        self.zx_editor = zx_editor

        ## New...
        btn = ttk.Button(
            master=self,
            text='New...',
            image='new-project', 
            compound=LEFT, 
            command=self.zx_editor.clicked_new
        )
        btn.grid(row=0, column=0)

        ## Open...
        btn = ttk.Button(
            master=self,
            text='Open',
            image='open-project', 
            compound=LEFT, 
            command=self.zx_editor.clicked_open
        )
        btn.grid(row=0, column=1)

        ## Save
        btn = ttk.Button(
            master=self,
            text='Save',
            image='save-project', 
            compound=LEFT, 
            command=self.zx_editor.clicked_save
        )
        btn.grid(row=0, column=2)

        ## Open SCR...
        btn = ttk.Button(
            master=self, 
            text='Background', 
            image='set-background', 
            compound=LEFT, 
            command=self.zx_editor.clicked_background
        )
        btn.grid(row=0, column=3)

        ## configure scale
        self.scale_variable = ttk.IntVar()
        scale_options = ttk.Menu(self)
        for scale_up in range(1, (ZXEditor.SCALE_MAX + 1)):
            scale_options.add_radiobutton(
                label=f"{scale_up}x", 
                command=lambda scale_up=scale_up: self.zx_editor.set_scale(scale_up), 
                variable=self.scale_variable, 
                value=scale_up)
        self.scale_variable.set(self.zx_editor.scale)
        self.scale = ttk.Menubutton(
            master=self,
            text="Set scale",
            image='set-scale',
            compound=LEFT,
            menu=scale_options
        )
        self.scale.grid(row=0, column=4)

        ## Enable display grid
        self.button_grid = ttk.Button(
            master=self, 
            text='Grid', 
            image='grid-disabled', 
            compound=LEFT, 
            command=self.zx_editor.clicked_grid
        )
        self.button_grid.grid(row=0, column=5)

        ## Export options
        export_options = ttk.Menu(self)
        export_options.add_command(label="SCR", command=self.zx_editor.clicked_export_scr)
        export_options.add_command(label="SPECSCII", command=self.zx_editor.clicked_export_specscii)
        export_options.add_separator()
        export_options.add_command(label="Screenshot", command=self.zx_editor.clicked_save_screenshot)
        btn = ttk.Menubutton(
            master=self,
            text="Export",
            image='export',
            compound=LEFT,
            menu=export_options
        )
        btn.grid(row=0, column=6)        

    def notify_grid_changed(self, value):
        img_name = 'grid-disabled' if value else 'grid-enabled'
        self.button_grid.config(image=img_name)

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

        self.notify_scale_changed(self.zx_editor.scale)

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def notify_scale_changed(self, value):
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
    HIGHLIGHT_EFFECT_AVERAGE = 0
    HIGHLIGHT_EFFECT_DARKEN = 1

    def __init__(self, master):
        super().__init__(master)
        self.zx_editor = master
        self.default_fill = colorutils.color_to_rgb(master.master.style.colors.get('bg'))
        self.grid_colour = colorutils.color_to_rgb(master.master.style.colors.get('dark'))
        self.highlight_colour = colorutils.color_to_rgb(master.master.style.colors.get('danger'))
        self.label = ttk.Label(self)
        self.label.pack(padx=5, pady=5)
        self.in_focus = False

        self.notify_scale_changed(self.zx_editor.scale)
        self.label.bind('<Motion>', self.mouse_moved)
        self.label.bind('<Button-1>', self.mouse_clicked)
        self.label.bind('<Enter>', lambda x: self.set_custom_focus(True))
        self.label.bind('<Leave>', lambda x: self.set_custom_focus(False))

    def check_focus(self):
        return self.in_focus

    def set_custom_focus(self, in_focus):
        self.in_focus = in_focus
        style = 'raised' if in_focus else 'flat'
        self.label.config(relief=style)
        
        # Focus sometimes sticks to widgets, so we need to force it back to
        # ensure that using space doesn't additionally toggle widget values.
        if in_focus:
            self.focus_set()

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def create(self):
        colour = self.__get_fill_colour()
        self.pixel_data = numpy.full(shape=(self.__get_canvas_height(), self.__get_canvas_width(), 3), fill_value=colour, dtype=numpy.uint8)

    def __get_fill_colour(self):
        if self.zx_editor.is_grid_enabled:
            return self.grid_colour
        return self.default_fill

    def __get_canvas_width(self):
        num_pixels = ZXScreen.SCREEN_WIDTH_CHARS*8*self.zx_editor.scale
        num_pixels += ZXScreen.SCREEN_WIDTH_CHARS+1
        return num_pixels

    def __get_canvas_height(self):
        num_pixels = ZXScreen.SCREEN_HEIGHT_CHARS*8*self.zx_editor.scale
        num_pixels += ZXScreen.SCREEN_HEIGHT_CHARS+1
        return num_pixels

    def flip_canvas(self):
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

    def mouse_clicked(self, event):
        if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
            cursor_x, cursor_y = self.__get_cursor_from(event.x, event.y)
            if cursor_x >= 0 and cursor_y >= 0:
                self.zx_editor.move_cursor(cursor_x, cursor_y)

    def mouse_moved(self, event):
        # if event.x < self.pixel_data.shape[1] and event.y < self.pixel_data.shape[0]:
        #     char_x, char_y = self.__get_cursor_from(event.x, event.y)
        #     self.__highlight_cell(char_x, char_y, self.HIGHLIGHT_ACTIVE)
        #     self.refresh()
        pass

    def notify_cursor_changed(self, cursor_x, cursor_y):
        attr = self.zx_editor.zx_document.get_attribute(cursor_x, cursor_y)
        is_inverted = not self.zx_editor.zx_document.get_inverted(cursor_x, cursor_y) == ZXDocument.UNDEFINED
        self.zx_editor.sidebar.palette.from_data(attr, is_inverted)
        self.refresh()

    def notify_grid_changed(self, grid_enabled):
        self.create()
        self.refresh()

    def notify_scale_changed(self, scale_value):
        self.create()
        self.refresh()

    def refresh(self):
        self.pixel_data[:] = self.__get_fill_colour()

        rgb_data = self.zx_editor.zx_document.to_rgb()
        rgb_data = numpy.repeat(numpy.repeat(rgb_data, self.zx_editor.scale, axis=0), self.zx_editor.scale, axis=1)
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.__refresh_cell(char_x, char_y, rgb_data)
        self.__highlight_cell(self.zx_editor.cursor_x, self.zx_editor.cursor_y, self.highlight_colour)

        self.flip_canvas()

    def __refresh_cell(self, char_x, char_y, rgb_data):
        pix_x, pix_y, pix_size = self.__get_canvas_position(char_x, char_y)
        rgb_x, rgb_y, rgb_size = self.__get_screen_position(char_x, char_y)
        self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = rgb_data[rgb_y:rgb_y+rgb_size, rgb_x:rgb_x+rgb_size]

    def __highlight_cell(self, char_x, char_y, colour, highlight_effect=HIGHLIGHT_EFFECT_AVERAGE):
        if char_x == -1 or char_y == -1:
            return
        pix_x, pix_y, pix_size = self.__get_canvas_position(char_x, char_y)
        self.pixel_data[pix_y-1, pix_x-1:pix_x+pix_size+1] = colour
        self.pixel_data[pix_y+pix_size, pix_x-1:pix_x+pix_size+1] = colour
        self.pixel_data[pix_y-1:pix_y+pix_size, pix_x-1] = colour
        self.pixel_data[pix_y-1:pix_y+pix_size, pix_x+pix_size] = colour

        match highlight_effect:
            case self.HIGHLIGHT_EFFECT_AVERAGE:
                # average RGB between fill and contents
                fill = numpy.full(shape=(pix_size, pix_size, 3), fill_value=colour, dtype=numpy.uint8)
                self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = numpy.mean(numpy.array([self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size], fill]), axis=0)
            case self.HIGHLIGHT_EFFECT_DARKEN:
                # darken contents
                self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] = self.pixel_data[pix_y:pix_y+pix_size, pix_x:pix_x+pix_size] >> 1

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
    

class Sidebar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.palette = Palette(master=self, zx_editor=master)
        self.palette.pack(fill=X, pady=0)

        self.symbols = Symbols(self, zx_editor=master)
        self.symbols.pack(fill=X, pady=0)


class Palette(ttk.Frame):
    def __init__(self, master, zx_editor: ZXEditor):
        super().__init__(master, style='bg.TFrame')
        self.zx_editor = zx_editor
        self.is_bright = False
        self.is_bright_var = ttk.BooleanVar(master=self, value=self.is_bright)
        self.is_flash = False
        self.is_flash_var = ttk.BooleanVar(master=self, value=self.is_flash)
        self.is_inverted = False
        self.is_inverted_var = ttk.BooleanVar(master=self, value=self.is_inverted)
        self.is_sticky_enabled_var = ttk.BooleanVar(master=self, value=self.zx_editor.is_sticky_enabled)
        self.is_overwrite_enabled_var = ttk.BooleanVar(master=self, value=self.zx_editor.is_overwrite_enabled)
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


        frame = ttk.Frame(self)
        frame.grid(row=1, column=2, sticky=NSEW, padx=10)

        btn = ttk.Checkbutton(
            frame, 
            text="Bright", 
            bootstyle="square-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_bright_var,
            command=lambda: self.changed_bright(self.is_bright_var.get()))
        btn.grid(row=0, column=0, sticky=NW)

        btn = ttk.Checkbutton(
            frame, 
            text="Flashing", 
            bootstyle="square-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_flash_var,
            command=lambda: self.changed_flash(self.is_flash_var.get()))
        btn.grid(row=1, column=0, sticky=NW)

        self.btn_inverted = ttk.Checkbutton(
            frame, 
            text="Inverted", 
            bootstyle="square-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_inverted_var,
            command=lambda: self.changed_inverted(self.is_inverted_var.get()))
        self.btn_inverted.grid(row=2, column=0, sticky=NW)

        # When enabled we ignore updates to the palette when inserting data,
        # allowing us to lock a style for data entered.
        btn = ttk.Checkbutton(
            frame, 
            text="Keep attribute", 
            bootstyle="danger-round-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_sticky_enabled_var,
            command=lambda: self.zx_editor.set_sticky(self.is_sticky_enabled_var.get()))
        btn.grid(row=3, column=0, sticky=NW, pady=(10, 0))

        # Determines if we're overwriting the current highlighted cell or
        # advancing to the next position on write.
        btn = ttk.Checkbutton(
            frame, 
            text="Cursor overwrite", 
            bootstyle="danger-round-toggle",
            onvalue=True,
            offvalue=False,
            variable=self.is_overwrite_enabled_var,
            command=lambda: self.zx_editor.set_overwrite(self.is_overwrite_enabled_var.get()))
        btn.grid(row=4, column=0, sticky=NW)

    def changed_bright(self, value):
        self.is_bright = value
        self.zx_editor.set_cursor_attribute(self.get_attribute())
        self.refresh()

    def changed_flash(self, value):
        self.is_flash = value
        self.zx_editor.set_cursor_attribute(self.get_attribute())
        self.refresh()

    def changed_inverted(self, value):
        self.is_inverted = value
        self.zx_editor.set_cursor_inverted(self.get_inverted())
        self.refresh()

    def changed_ink(self, colour):
        self.current_ink = colour
        self.zx_editor.set_cursor_attribute(self.get_attribute())
        self.refresh()

    def changed_paper(self, colour):
        self.current_paper = colour
        self.zx_editor.set_cursor_attribute(self.get_attribute())
        self.refresh()

    def from_data(self, attribute, is_inverted):
        if self.zx_editor.is_sticky_enabled:
            return
        parsed = ZXScreen.to_parsed_attribute(attribute)
        self.is_bright = parsed['bright']
        self.is_flash = parsed['flash']
        self.current_ink = parsed['ink']
        self.current_paper = parsed['paper']
        self.is_inverted = is_inverted
        self.refresh()

    def get_attribute(self):
        return ZXScreen.to_attribute(
            self.is_flash, 
            self.is_bright, 
            self.current_paper, 
            self.current_ink)
    
    def get_dataset(self):
        return PaletteData(self.get_attribute(), self.get_inverted())

    def get_inverted(self):
        '''
        While scripts may care otherwise, the editor only deals with inverted
        as either on or not defined at all. This was done in order to ensure
        that we're not flipping things in invisible cells.
        '''
        if self.is_inverted:
            return True
        return ZXDocument.UNDEFINED

    def notify_scale_changed(self, value):
        pass

    def notify_overwrite_changed(self, value):
        self.is_overwrite_enabled_var.set(value)

    def notify_sticky_changed(self, value):
        self.is_sticky_enabled_var.set(value)

    def refresh(self):
        self.is_bright_var.set(self.is_bright)
        self.is_flash_var.set(self.is_flash)
        self.is_inverted_var.set(self.is_inverted)
        for widget in self.ink_widgets:
            widget.refresh()
        for widget in self.paper_widgets:
            widget.refresh()
    

class PaletteData():
    def __init__(self, attribute, is_inverted):
        self.attribute = attribute
        self.is_inverted = is_inverted

    def __str__(self):
        token_string = ' '.join(str(x) for x in self.to_tokens())
        return "{} ({})".format(
            'format',
            token_string
        )

    def to_tokens(self):
        if not self.is_inverted == ZXDocument.UNDEFINED:
            return [f"INVERTED={int(self.is_inverted)}"] + ZXScreen.to_tokens(self.attribute)
        return ZXScreen.to_tokens(self.attribute)
    

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
            self.palette.changed_ink(self.colour)
        if self.type == self.TYPE_PAPER:
            self.palette.changed_paper(self.colour)

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

    
class Symbols(ttk.Frame):
    NUM_COLUMNS = 8

    def __init__(self, master, zx_editor):
        super().__init__(master, style='bg.TFrame')
        self.zx_editor = zx_editor

        self.font_frame = ttk.Frame(self, padding=5, style="bg.TFrame")
        self.font_frame.pack()
        self.font_widgets = []

        self.glyph_frame = ttk.Frame(self, padding=5, style="bg.TFrame")
        self.glyph_frame.pack()
        self.glyph_widgets = []

    def load_font(self, path, frame, widgets, value_offset):
        font_data = ZXFont.from_file(path, rgb_fg=self.__get_colour('fg'), rgb_bg=self.__get_colour('bg'), generate_rgb=True)
        
        # Remove existing elements
        for widget in widgets:
            widget.destroy()
        widgets.clear()

        # Add new ones
        grid_row = 0
        grid_column = 0
        for char_index in range(font_data.get_glyph_count()):
            widget = Glyph(frame, self.zx_editor, char_index, value_offset, scale_mode=3)
            widget.render_rgb(font_data.get_offset_rgb(char_index))
            widget.flip_canvas()
            widget.grid(row=grid_row, column=grid_column, padx=0, pady=0)

            grid_column += 1
            if grid_column == self.NUM_COLUMNS:
                grid_column = 0
                grid_row += 1
            widgets.append(widget)   

    def __get_colour(self, color_label):
        return colorutils.color_to_rgb(self.zx_editor.master.style.colors.get(color_label))

    def notify_font_changed(self, font_path):
        self.load_font(font_path, self.font_frame, self.font_widgets, ZXFont.FONT_OFFSET)

    def notify_glyph_changed(self, glyph_path):
        self.load_font(glyph_path, self.glyph_frame, self.glyph_widgets, ZXGlyph.GLYPH_OFFSET)

    def notify_scale_changed(self, value):
        for widget in self.font_widgets:
            widget.notify_scale_changed(value)

class Glyph(Canvas):
    def __init__(self, master, zx_editor, glyph_idx, value_offset, scale_mode=0):
        super().__init__(master, zx_editor, view_width=8, view_height=8, scale_mode=scale_mode, label_padx=0, label_pady=0)
        self.glyph_idx = glyph_idx
        self.value_offset = value_offset
        self.label.bind('<Button-1>', self.mouse_clicked)
        self.label.bind('<Enter>', self.mouse_hover)
        self.label.bind('<Leave>', self.mouse_exit)

    def mouse_clicked(self, event):
        self.zx_editor.set_cursor_character(self.__get_char_code())

    def __get_char_code(self):
        return (self.glyph_idx + self.value_offset)

    def mouse_hover(self, event):
        self.label.config(relief='raised')

    def mouse_exit(self, event):
        self.label.config(relief='flat')


class Status(ttk.Frame):
    def __init__(self, master, zx_editor):
        super().__init__(master, style='dark.TFrame')
        self.zx_editor = zx_editor
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

        self.notify_cursor_changed(self.zx_editor.cursor_x, self.zx_editor.cursor_y)

    def set_status(self, message=''):
        self.setvar('status-text', message)

    def notify_cursor_changed(self, cursor_x, cursor_y):
        self.setvar(
            'status-position', 
            'Cursor: ({},{})'.format(
                str(cursor_x).rjust(2, '0'), 
                str(cursor_y).rjust(2, '0')))

if __name__ == '__main__':
    app = ttk.Window(ZXEditor.PROGRAM_TITLE, themename="darkly")
    zx_editor = ZXEditor(app)
    app.protocol("WM_DELETE_WINDOW", lambda app=app: zx_editor.on_quit(app))
    app.mainloop()
