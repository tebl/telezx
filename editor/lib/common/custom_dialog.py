from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
import webbrowser

class CustomDialog(Dialog):
    def __init__(self, master, title):
        super().__init__(master, title=title)
        self.custom_pad_y = 3
        self.custom_pad_x = 10
        self.custom_pad_border = 20

    def create_buttonbox(self, master):
        pass

    def open_url(self, url_path):
        webbrowser.open(url_path)
