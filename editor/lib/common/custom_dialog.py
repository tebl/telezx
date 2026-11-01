from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
import webbrowser, typing

class CustomDialog(Dialog):
    def __init__(self, master, title):
        super().__init__(master, title=title)
        self.custom_pad_y = 3
        self.custom_pad_x = 10
        self.custom_pad_border = 20

    def close(self):
        self._toplevel.destroy()

    def create_buttonbox(self, master):
        pass

    @classmethod
    def open_url(cls, url_path):
        webbrowser.open(url_path)