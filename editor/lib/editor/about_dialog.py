from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk

from .custom_dialog import CustomDialog


class AboutDialog(CustomDialog):
    def __init__(self, master, zx_editor):
        super().__init__(master, zx_editor, title="About")


    def create_body(self, master):
        lbl = ttk.Label(master, image='logo', justify=CENTER)
        lbl.pack(expand=True, padx=self.custom_pad_x, pady=(self.custom_pad_border, self.custom_pad_y))

        lbl = ttk.Label(master, text=self.zx_editor.PROGRAM_TITLE)
        lbl.pack(padx=self.custom_pad_x, pady=self.custom_pad_y)

        lbl = ttk.Label(master, text=self.zx_editor.PROGRAM_COPYRIGHT)
        lbl.pack(padx=self.custom_pad_x, pady=0)

        lbl = ttk.Button(master, text=self.zx_editor.PROGRAM_URL, style="info link", command=lambda: self.open_url(self.zx_editor.PROGRAM_URL))
        lbl.pack(padx=self.custom_pad_x, pady=0)

        lbl = ttk.Label(master, text=self.zx_editor.PROGRAM_LICENSE, justify=CENTER)
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_y, self.custom_pad_border))
