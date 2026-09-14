from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk

from .custom_dialog import CustomDialog

class KeyboardDialog(CustomDialog):
    def __init__(self, master, zx_editor):
        super().__init__(master, zx_editor, title="Keyboard")

    def create_body(self, master):
        main = ttk.Frame(master)
        main.pack()
        main.columnconfigure(0, weight=10, uniform='tag')
        main.columnconfigure(1, weight=1, uniform='tag')
        main.columnconfigure(2, weight=10, uniform='tag')
        self.__create_section(
            'Shortcuts', 
            main, 0, 0,
            [
                ('Ctrl', None, 'n', 'New document'),
                ('Ctrl', None, 'o', 'Open document'),
                ('Ctrl', None, 's', 'Save document'),
                ('Ctrl', None, 'b', 'Set background'),
                ('Ctrl', None, 'g', 'Toggle grid display'),
                ('Ctrl', None, 'q', 'Quit'),
            ])

        self.__create_section(
            'Copy & Paste', 
            main, 0, 2,
            [
                ('Ctrl', None, 'c', 'Copy selected cells'),
                ('Ctrl', None, 'x', 'Cut selected cells'),
                ('Ctrl', None, 'v', 'Paste cell'),
                ('Ctrl', None, 'z', 'Undo changes'),
            ])

        self.__create_section(
            'Attribute manipulation', 
            main, 1, 0,
            [
                ('Ctrl', None, 'f', 'Follow attribute memory'),
                ('Ctrl', None, 'i', 'Invert cell'),
                ('Ctrl', 'Shift', 'f', 'Swap ink/paper'),
                ('Ctrl', 'Shift', 'c', 'Copy cell attribute'),
                ('Ctrl', 'Shift', 'v', 'Paste cell attribute')
            ])

        self.__create_section(
            'Content manipulation', 
            main, 1, 2,
            [
                (None, 'Shift', 'LMB', 'Set selection'),
                ('Ctrl', None, 'UP', 'Move selected cells up'),
                ('Ctrl', None, 'DOWN', 'Move selected cells down'),
                ('Ctrl', None, 'LEFT', 'Move selected cells left'),
                ('Ctrl', None, 'RIGHT', 'Move selected cells right'),
                (None, 'Shift', 'UP', 'Shift selected cells up'),
                (None, 'Shift', 'DOWN', 'Shift selected cells down'),
                (None, 'Shift', 'LEFT', 'Shift selected cells left'),
                (None, 'Shift', 'RIGHT', 'Shift selected cells right')
            ])

    def __create_section(self, title: str, parent: ttk.Frame, grid_row: int, grid_column: int, items):
        content = ttk.Frame(parent)
        content.grid(row=grid_row, column=grid_column, sticky=N)

        lbl = ttk.Label(content, text=title, justify=CENTER)
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_border, self.custom_pad_y))

        list_frame = ttk.Frame(content)
        list_frame.pack(padx=self.custom_pad_x, pady=(self.custom_pad_y, self.custom_pad_border), fill=BOTH, expand=True)

        self.__create_list(list_frame, items)

    def __create_list(self, list_frame, items):
        for idx, item in enumerate(items):
            if item is None:
                lbl = ttk.Label(list_frame, text=' ')
                lbl.grid(row=idx, column=0)
                continue
            key_1, key_2, key_3, description = item

            if key_1:
                lbl = ttk.Label(list_frame, text=' ' + key_1, style="inverse-dark", relief="groove")
                lbl.grid(row=idx, column=0, padx=0, ipadx=self.custom_pad_y, ipady=2)

            if key_1 and key_2:
                lbl = ttk.Label(list_frame, text='+', style="secondary")
                lbl.grid(row=idx, column=1, padx=0)

            if key_2:
                lbl = ttk.Label(list_frame, text=' ' + key_2, style="inverse-dark", relief="groove")
                lbl.grid(row=idx, column=2, padx=0, ipadx=self.custom_pad_y, ipady=2)

            lbl = ttk.Label(list_frame, text='+', style="secondary")
            lbl.grid(row=idx, column=3, padx=0, sticky=W)
            lbl = ttk.Label(list_frame, text=' ' + key_3, style="inverse-dark", relief="groove")
            lbl.grid(row=idx, column=4, padx=0, sticky=W, ipadx=self.custom_pad_y, ipady=2)

            lbl = ttk.Label(list_frame, text=description)
            lbl.grid(row=idx, column=6, sticky=W, padx=self.custom_pad_x)
