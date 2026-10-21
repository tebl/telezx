import numpy
import traceback
import string
from abc import ABC, abstractmethod
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap import colorutils
import ttkbootstrap as ttk
from pathlib import Path
from PIL import Image, ImageTk

from . import utilities
from .zx_logger import ZXLogger

class BaseEditor(ttk.Frame):
    PROGRAM_TITLE = 'ZX Editor'
    PROGRAM_URL = 'https://github.com/tebl/telezx'
    PROGRAM_COPYRIGHT = "Copyright © 2026 Tor-Eirik Bakke Lunde"
    PROGRAM_LICENSE_URL = f'{PROGRAM_URL}/blob/main/LICENSE.md'
    PROGRAM_LICENSE = "This application comes with absolutely no warranty.\nSee the GNU General Public Licence, version 3 or later for details."
    PROGRAM_LICENSE_FULL = '''\
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <https://www.gnu.org/licenses/>.'''

    FILE_TYPE = 'ZXToken'
    FILE_EXTENSION = '.zxtoken'

    TITLEBAR_REFRESH = 250

    def __init__(self, *args, **kwargs):
        self.debug_enabled: bool=kwargs.pop('debug_enabled', False)
        super().__init__(*args, **kwargs)
        if self.debug_enabled:
            ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)
        self._load_assets()

    def _allow_discard(self, title):
        return Messagebox.okcancel(parent=self, title=title, message='Document has unsaved changes, do you want to discard these?')

    @abstractmethod
    def _load_assets(self, image_files: dict[str, str]):
        self.photoimages = []        
        img_path = utilities.get_project_root() / 'assets'
        for key, val in image_files.items():
            _path = img_path / val
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))

    @abstractmethod
    def _get_title(self) -> str:
        '''
        Called from update_title_periodic, should return the document name for
        inclusion in the program title.
        '''
        ...

    @abstractmethod
    def on_delete_window(self, root):
        '''
        Exit the program, any inheriting classes should clean up any hanging
        resources before returning.
        '''
        root.destroy()

    def update_title_periodic(self):
        self.__update_title()
        self.after(self.TITLEBAR_REFRESH, self.update_title_periodic)

    def __update_title(self):
        self.master.title(
            "{} ({})".format(
                self.PROGRAM_TITLE, 
                self._get_title()
            )
        )
