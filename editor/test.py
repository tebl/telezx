from datetime import datetime
from random import choices
import ttkbootstrap as ttk
from ttkbootstrap.style import Bootstyle
from tkinter.filedialog import askdirectory
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import numpy

from lib import ZXScreen
from PIL import Image, ImageTk


PATH = Path(__file__).parent / 'assets'


class ZXEditor(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.__load_assets()

        self.scale = 3
        self.zx = ZXScreen()

        self.buttonbar = Menubar(self)
        self.buttonbar.pack(fill=X, pady=1, side=TOP)

        self.sidebar = Sidebar(self)
        self.sidebar.pack(side=RIGHT, fill=Y)

        self.highlight = Highlight(self.sidebar)
        self.highlight.pack(fill=X, pady=1)

        self.symbols = Symbols(self.sidebar)
        self.symbols.pack(fill=X, pady=1)

        self.display = DisplayArea(self)
        self.display.pack(side=LEFT, fill=BOTH)

    def clicked_new(self):
        print("Clear")

    def clicked_scr(self):
        print("Open SCR")

    def set_scale(self, value):
        self.scale = value
        self.display.configure_scale(value)

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


class Menubar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='primary.TFrame')

        ## New...
        btn = ttk.Button(
            master=self, text='New...',
            image='new-light', 
            compound=LEFT, 
            command=self.master.clicked_new
        )
        btn.pack(side=LEFT, ipadx=5, ipady=5, padx=(1, 0), pady=1)

        ## Open SCR...
        btn = ttk.Button(
            master=self, 
            text='Open SCR', 
            image='opened-folder', 
            compound=LEFT, 
            command=self.master.clicked_scr
        )
        btn.pack(side=LEFT, ipadx=5, ipady=5, padx=0, pady=1)

        ## configure scale
        scale_options = ttk.Menu(self)
        scale_options.add_radiobutton(label="1x", command=lambda: self.set_scale(1))
        scale_options.add_radiobutton(label="2x", command=lambda: self.set_scale(2))
        scale_options.add_radiobutton(label="3x", command=lambda: self.set_scale(3))
        self.scale = ttk.Menubutton(
            master=self,
            text="Set scale",
            menu=scale_options
        )
        self.scale.pack(side=LEFT, ipadx=5, ipady=5, padx=0, pady=1)

    def set_scale(self, value):
        self.scale.config(text=f'{value}x')
        self.master.set_scale(value)

class CollapsingFrame(ttk.Frame):
    """A collapsible frame widget that opens and closes with a click."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.cumulative_rows = 0

        # widget images
        self.images = [
            ttk.PhotoImage(file=PATH/'icons8_double_up_24px.png'),
            ttk.PhotoImage(file=PATH/'icons8_double_right_24px.png')
        ]

    def add(self, child, title="", bootstyle=PRIMARY, **kwargs):
        """Add a child to the collapsible frame

        Parameters:

            child (Frame):
                The child frame to add to the widget.

            title (str):
                The title appearing on the collapsible section header.

            bootstyle (str):
                The style to apply to the collapsible section header.

            **kwargs (Dict):
                Other optional keyword arguments.
        """
        if child.winfo_class() != 'TFrame':
            return
        
        style_color = Bootstyle.ttkstyle_widget_color(bootstyle)
        frm = ttk.Frame(self, bootstyle=style_color)
        frm.grid(row=self.cumulative_rows, column=0, sticky=EW)

        # header title
        header = ttk.Label(
            master=frm,
            text=title,
            bootstyle=(style_color, INVERSE)
        )
        if kwargs.get('textvariable'):
            header.configure(textvariable=kwargs.get('textvariable'))
        header.pack(side=LEFT, fill=BOTH, padx=10)

        # header toggle button
        def _func(c=child): return self._toggle_open_close(c)
        btn = ttk.Button(
            master=frm,
            image=self.images[0],
            bootstyle=style_color,
            command=_func
        )
        btn.pack(side=RIGHT)

        # assign toggle button to child so that it can be toggled
        child.btn = btn
        child.grid(row=self.cumulative_rows + 1, column=0, sticky=NSEW)

        # increment the row assignment
        self.cumulative_rows += 2

    def _toggle_open_close(self, child):
        """Open or close the section and change the toggle button 
        image accordingly.

        Parameters:
            
            child (Frame):
                The child element to add or remove from grid manager.
        """
        if child.winfo_viewable():
            child.grid_remove()
            child.btn.configure(image=self.images[1])
        else:
            child.grid()
            child.btn.configure(image=self.images[0])


class DisplayArea(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.default_fill = 0xc0
        self.view_width = self.master.zx.SCREEN_WIDTH_PIXELS
        self.view_height = self.master.zx.SCREEN_HEIGHT_PIXELS

        self.label = ttk.Label(self)
        self.label.pack(padx=5, pady=5)

        self.configure_scale(self.master.scale)

    def clear(self):
        self.pixel_data[:] = self.default_fill

    def configure_scale(self, value):
        self.pixel_data = numpy.full(shape=(self.view_height*value, self.view_width*value, 3), fill_value=self.default_fill, dtype=numpy.uint8)
        self.update()

    def update(self):
        # self.render_canvas()
        pil_img = Image.fromarray(self.pixel_data)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

class Sidebar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='bg.TFrame')


class Highlight(CollapsingFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        frame = ttk.Frame(self, padding=5)
        frame.columnconfigure(1, weight=1)
        self.add(
            child=frame, 
            title='Highlight', 
            bootstyle=INFO
        )

        ## destination
        lbl = ttk.Label(frame, text='Destination:')
        lbl.grid(row=0, column=0, sticky=W, pady=2)
        lbl = ttk.Label(frame, textvariable='destination')
        lbl.grid(row=0, column=1, sticky=EW, padx=5, pady=2)
        self.setvar('destination', 'd:/test/')

        ## last run
        lbl = ttk.Label(frame, text='Last Run:')
        lbl.grid(row=1, column=0, sticky=W, pady=2)
        lbl = ttk.Label(frame, textvariable='lastrun')
        lbl.grid(row=1, column=1, sticky=EW, padx=5, pady=2)
        self.setvar('lastrun', '14.06.2021 19:34:43')

        ## files Identical
        lbl = ttk.Label(frame, text='Files Identical:')
        lbl.grid(row=2, column=0, sticky=W, pady=2)
        lbl = ttk.Label(frame, textvariable='filesidentical')
        lbl.grid(row=2, column=1, sticky=EW, padx=5, pady=2)
        self.setvar('filesidentical', '15%')


class Symbols(CollapsingFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        frame = ttk.Frame(self, padding=10)
        frame.columnconfigure(1, weight=1)
        self.add(
            child=frame, 
            title='Symbols', 
            bootstyle=INFO
        )

        btn = ttk.Button(
            master=frame, 
            text='Stop', 
            compound=LEFT
        )
        btn.grid(row=0, column=0, columnspan=2, sticky=W)

        lbl = ttk.Label(frame, text="Loaded:")
        lbl.grid(row=1, column=0, sticky=W)
        lbl = ttk.Label(frame, textvariable='symbols-count')
        lbl.grid(row=1, column=1, sticky=W)
        self.setvar('symbols-count', '33')


if __name__ == '__main__':
    app = ttk.Window("ZX Editor")
    ZXEditor(app)
    app.mainloop()
