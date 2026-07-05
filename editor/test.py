from datetime import datetime
from random import choices
import ttkbootstrap as ttk
from ttkbootstrap.style import Bootstyle
from tkinter.filedialog import askdirectory
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from tkinter.scrolledtext import ScrolledText
from pathlib import Path


PATH = Path(__file__).parent / 'assets'


class ZXEditor(ttk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)

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

        buttonbar = Menubar(self)
        buttonbar.pack(fill=X, pady=1, side=TOP)

        # sidebar panel
        sidebar = Sidebar(self)
        sidebar.pack(side=RIGHT, fill=Y)

        highlight = Highlight(sidebar)
        highlight.pack(fill=X, pady=1)

        symbols = Symbols(sidebar)
        symbols.pack(fill=BOTH, pady=1)




        # Main editor
        main_panel = ttk.Frame(self, padding=(2, 1))
        main_panel.pack(side=RIGHT, fill=BOTH, expand=YES)



        ## scrolling text output
        scroll_cf = CollapsingFrame(main_panel)
        scroll_cf.pack(fill=BOTH, expand=YES)
        
        output_container = ttk.Frame(scroll_cf, padding=1)
        _value = 'Log: Backing up... [Uploading file: D:/sample_file_35.txt]'
        self.setvar('scroll-message', _value)
        st = ScrolledText(output_container)
        st.pack(fill=BOTH, expand=YES)
        scroll_cf.add(output_container, textvariable='scroll-message')



        ## Treeview
        tv = ttk.Treeview(main_panel, show='headings', height=5)
        tv.configure(columns=(
            'name', 'state', 'last-modified', 
            'last-run-time', 'size'
        ))
        tv.column('name', width=150, stretch=True)
        
        for col in ['last-modified', 'last-run-time', 'size']:
            tv.column(col, stretch=False)
        
        for col in tv['columns']:
            tv.heading(col, text=col.title(), anchor=W)
        
        tv.pack(fill=X, pady=1)



        ## treeview and backup logs
        for x in range(20, 35):
            result = choices(['Backup Up', 'Missed in Destination'])[0]
            st.insert(END, f'19:34:{x}\t\t Uploading: D:/file_{x}.txt\n')
            st.insert(END, f'19:34:{x}\t\t Upload {result}.\n')
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            tv.insert('', END, x, 
                      values=(f'sample_file_{x}.txt', 
                              result, timestamp, timestamp, 
                              f'{int(x // 3)} MB')
            )
        tv.selection_set(20)


class Menubar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='primary.TFrame')

        ## new backup
        _func = lambda: Messagebox.ok(message='Adding new backup')
        btn = ttk.Button(
            master=self, text='New...',
            image='new-light', 
            compound=LEFT, 
            command=_func
        )
        btn.pack(side=LEFT, ipadx=5, ipady=5, padx=(1, 0), pady=1)

        ## backup
        _func = lambda: Messagebox.ok(message='Backing up...')
        btn = ttk.Button(
            master=self, 
            text='Open SCR', 
            image='opened-folder', 
            compound=LEFT, 
            command=_func
        )
        btn.pack(side=LEFT, ipadx=5, ipady=5, padx=0, pady=1)

        ## configure scale
        menu = ttk.Menu(self)
        menu.add_radiobutton(label="1x", value=1)
        menu.add_radiobutton(label="2x", value=2)
        menu.add_radiobutton(label="3x", value=3)
        scale = ttk.Menubutton(
            master=self,
            text="Set scale",
            menu=menu
        )
        scale.pack(side=LEFT, ipadx=5, ipady=5, padx=0, pady=1)

        ## settings
        # _func = lambda: Messagebox.ok(message='Changing settings')
        # btn = ttk.Button(
        #     master=buttonbar, 
        #     text='Settings', 
        #     image='settings-light',
        #     compound=LEFT, 
        #     command=_func
        # )
        # btn.pack(side=LEFT, ipadx=5, ipady=5, padx=0, pady=1)


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
