from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk

class BaseMenu(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(style='primary.TFrame', *args, **kwargs)
        self.__next_id = 0

    def _next_column(self) -> int:
        self.__next_id += 1
        return (self.__next_id - 1)
