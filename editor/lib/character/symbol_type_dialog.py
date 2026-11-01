import typing
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from .. import CustomDialog
from .zx_symbol_collection import ZXFontCollection, ZXGlyphCollection

class SymbolTypeDialog(CustomDialog):
    def __init__(self, master, title, selected: str|None=None, confirm_discard: bool=False):
        super().__init__(master, title=title)
        self.initial_selected = selected
        self.confirm_discard = confirm_discard
        self.var_document = ttk.StringVar()
        self.var_confirm = ttk.BooleanVar(value=False)
        self.custom_pad_y = 3
        self.custom_pad_x = 10
        self.custom_pad_border = 15

    def create_body(self, master):
        frame = ttk.Frame(master)
        frame.pack(fill=X, expand=YES, padx=10, pady=(15, 5))

        # Ensures that we're always selecting the first option, but allow
        # updates to the value if we enconter one with the specified initial
        # value.
        first = True
        for document_type, description in self.__options():
            if first or document_type == self.initial_selected:
                self.var_document.set(document_type)
            first = False

        for document_type, description in self.__options():
            radio = ttk.Radiobutton(frame, 
                                    text=description, 
                                    value=document_type,
                                    variable=self.var_document)
            radio.pack(anchor=W, padx=self.custom_pad_x, pady=0)

        if self.confirm_discard:
            confirm = ttk.Checkbutton(frame, 
                                    text="Discard current project", 
                                    variable=self.var_confirm,
                                    bootstyle=DANGER,
                                    command=self.on_confirm)
            confirm.pack(anchor=W, padx=self.custom_pad_x, pady=10)

        ttk.Separator(master).pack(fill=X, expand=True, pady=self.custom_pad_y)
        return frame

    def __options(self):
        for collection in [ZXFontCollection, ZXGlyphCollection]:
            yield (collection.__name__, collection.get_type_description())

    def create_buttonbox(self, master):
        frame = ttk.Frame(master)
        frame.pack(fill=X, expand=YES)

        btn_padx = (0, 5)
        btn_pady = (0, 5)
        self.btn_ok = ttk.Button(frame, 
                            text='OK',
                            width=6,
                            bootstyle=self.__btn_ok_style(),
                            command=self.on_ok)
        self.btn_ok.pack(side=RIGHT, padx=btn_padx, pady=btn_pady)
        self.btn_ok.focus_set()

        self.btn_cancel = ttk.Button(frame, 
                                text='Cancel',
                                width=6,
                                bootstyle=SECONDARY,
                                command=self.on_cancel)
        self.btn_cancel.pack(side=RIGHT, padx=btn_padx, pady=btn_pady)

    def __btn_ok_style(self):
        return SECONDARY if self.confirm_discard and not self.var_confirm.get() else PRIMARY

    def on_cancel(self, event=None):
        self._result = None
        self.close()

    def on_confirm(self, event=None):
        self.btn_ok.configure(bootstyle=self.__btn_ok_style())

    def on_ok(self, event=None):
        if self.confirm_discard and not self.var_confirm.get():
            return 'break'
        self._result = self.var_document.get()
        self.close()

    @classmethod
    def get_result(cls, master, title: str, selected: str|None=None, confirm_discard: bool=False) -> typing.Any:
        dialog = cls(master, 
                     title=title, 
                     selected=selected,
                     confirm_discard=confirm_discard)
        dialog.show(wait_for_result=True)
        return dialog.result