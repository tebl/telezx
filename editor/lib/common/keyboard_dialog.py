from abc import ABC, abstractmethod
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

    @abstractmethod
    def create_body(self, master):
        main = ttk.Frame(master)
        main.pack()
        return main

    def _create_section(self, title: str, parent: ttk.Frame, grid_row: int, grid_column: int, items: list, key_width: int=50, spacer_width: int=10):
        content = ttk.Frame(parent)
        content.grid(row=grid_row, column=grid_column, sticky=NW)

        lbl = ttk.Label(content, text=f'{title}:', style='default')
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_border, self.custom_pad_y), fill=X, anchor=N)

        list_frame = ttk.Frame(content)
        list_frame.pack(padx=self.custom_pad_x, pady=(self.custom_pad_y, self.custom_pad_border), fill=BOTH, expand=True)

        list_frame.columnconfigure(0, minsize=key_width, uniform='key')
        list_frame.columnconfigure(1, minsize=spacer_width, uniform='spacer')
        list_frame.columnconfigure(2, minsize=key_width, uniform='key')
        list_frame.columnconfigure(3, minsize=spacer_width, uniform='spacer')
        list_frame.columnconfigure(4, minsize=key_width)

        self.__create_list(list_frame, items)

    def __create_list(self, list_frame, items):
        for idx, item in enumerate(items):
            if item is None:
                lbl = ttk.Label(list_frame, text=' ')
                lbl.grid(row=idx, column=0)
                continue
            key_1, key_2, key_3, description = item

            if key_1:
                lbl = ttk.Label(list_frame, text=key_1, style="inverse-dark", relief="groove", anchor='center')
                lbl.grid(row=idx, column=0, padx=0, pady=2, sticky=W, ipadx=self.custom_pad_y, ipady=2)

            if key_1 and (key_2):
                lbl = ttk.Label(list_frame, text='+ ', style="secondary")
                lbl.grid(row=idx, column=1, padx=0, pady=2, sticky=W)

            if key_2:
                lbl = ttk.Label(list_frame, text=' ' + key_2, style="inverse-dark", relief="groove", anchor='center')
                lbl.grid(row=idx, column=2, padx=0, pady=2, sticky=W, ipadx=self.custom_pad_y, ipady=2)

            if key_3 and (key_1 or key_2):
                lbl = ttk.Label(list_frame, text='+ ', style="secondary")
                lbl.grid(row=idx, column=3, padx=0, pady=2, sticky=W)

            if key_3:
                lbl = ttk.Label(list_frame, text=' ' + key_3, style="inverse-dark", relief="groove", anchor='center')
                lbl.grid(row=idx, column=4, padx=0, pady=2, sticky=W, ipadx=self.custom_pad_y, ipady=2)

            lbl = ttk.Label(list_frame, text=description, style='default' if (key_1 or key_2 or key_3) else 'primary')
            lbl.grid(row=idx, column=6, sticky=W, padx=self.custom_pad_x)
