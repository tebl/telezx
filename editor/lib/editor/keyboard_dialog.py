from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk

from .custom_dialog import CustomDialog

class KeyboardDialog(CustomDialog):
    def __init__(self, master):
        super().__init__(master, title="Keyboard")

    def create_body(self, master):
        lbl = ttk.Label(master, text="Overview", justify=CENTER)
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_border, self.custom_pad_y))

        frame = ttk.Frame(master)
        frame.pack(padx=self.custom_pad_x, pady=(self.custom_pad_y, self.custom_pad_border), fill=BOTH, expand=True)

        items = [
            ('Ctrl', None, 'n', 'New document'),
            ('Ctrl', None, 'o', 'Open document'),
            ('Ctrl', None, 's', 'Save document'),
            ('Ctrl', None, 'b', 'Set background'),
            ('Ctrl', None, 'g', 'Toggle grid display'),
            ('Ctrl', None, 'f', 'Follow attribute memory'),
            ('Ctrl', None, 'q', 'Quit'),
            ('Ctrl', None, 'i', 'Invert cell'),
            ('Ctrl', None, 'c', 'Copy cell'),
            ('Ctrl', None, 'v', 'Paste cell'),
            ('Ctrl', 'Shift', 'c', 'Copy cell attribute'),
            ('Ctrl', 'Shift', 'v', 'Paste cell attribute'),
            ('Ctrl', 'Shift', 'f', 'Swap ink/paper'),
            ('Ctrl', None, 'UP', 'Move selected cells up'),
            ('Ctrl', None, 'DOWN', 'Move selected cells down'),
            ('Ctrl', None, 'LEFT', 'Move selected cells left'),
            ('Ctrl', None, 'RIGHT', 'Move selected cells right'),
            (None, 'Shift', 'UP', 'Shift selected cells up'),
            (None, 'Shift', 'DOWN', 'Shift selected cells down'),
            (None, 'Shift', 'LEFT', 'Shift selected cells left'),
            (None, 'Shift', 'RIGHT', 'Shift selected cells right')
        ]
        for idx, item in enumerate(items):
            key_1, key_2, key_3, description = item

            if key_1:
                lbl = ttk.Label(frame, text=' ' + key_1, style="inverse-dark", relief="groove")
                lbl.grid(row=idx, column=0, padx=0, ipadx=self.custom_pad_y, ipady=2)

            if key_1 and key_2:
                lbl = ttk.Label(frame, text='+', style="secondary")
                lbl.grid(row=idx, column=1, padx=0)

            if key_2:
                lbl = ttk.Label(frame, text=' ' + key_2, style="inverse-dark", relief="groove")
                lbl.grid(row=idx, column=2, padx=0, ipadx=self.custom_pad_y, ipady=2)

            lbl = ttk.Label(frame, text='+', style="secondary")
            lbl.grid(row=idx, column=3, padx=0, sticky=W)
            lbl = ttk.Label(frame, text=' ' + key_3, style="inverse-dark", relief="groove")
            lbl.grid(row=idx, column=4, padx=0, sticky=W, ipadx=self.custom_pad_y, ipady=2)

            lbl = ttk.Label(frame, text=description)
            lbl.grid(row=idx, column=6, sticky=W, padx=self.custom_pad_x)
