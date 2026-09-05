from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk

from .custom_dialog import CustomDialog

class LicenseDialog(CustomDialog):
    def __init__(self, master):
        super().__init__(master, title="License")

    def create_body(self, master):
        lbl = ttk.Label(master, text=self.master.PROGRAM_TITLE, justify=CENTER)
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_border, self.custom_pad_y))

        lbl = ttk.Label(master, text=self.master.PROGRAM_COPYRIGHT)
        lbl.pack(padx=self.custom_pad_x, pady=0)

        lbl = ttk.Label(master, text=self.get_license_text())
        lbl.pack(padx=self.custom_pad_x, pady=0)

        lbl = ttk.Button(master, text="Open LICENSE.md", style="info link", command=lambda: self.open_url(self.master.PROGRAM_LICENSE_URL))
        lbl.pack(padx=self.custom_pad_x, pady=(self.custom_pad_y, self.custom_pad_border))

    def get_license_text(self):
        return "\n".join(
            [line.strip() for line in self.master.PROGRAM_LICENSE_FULL.splitlines()]
        )
