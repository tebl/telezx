import numpy, typing
from abc import ABC, abstractmethod
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from .. import ZXAttribute, ZXBorder, ZXToken, ZXFont, ZXScreen
from .custom_dialog import CustomDialog

class BaseAttributeDialog(CustomDialog):
    def __init__(self, master, title, current: ZXAttribute|None=None, border: ZXBorder|None=None, enable_preview: bool=True):
        super().__init__(master, title=title)
        self.enable_preview = enable_preview
        self.attribute = self._extract_attribute(current)
        self.border = self._extract_border(border)
        self.preview = AttributePreview(self)
        self._next_row = 0

    def get_next_row(self) -> int:
        self._next_row += 1
        return (self._next_row - 1)

    def create_buttonbox(self, master):
        frame = ttk.Frame(master)
        frame.pack(fill=X, expand=YES)

        btn_padx = (0, 5)
        btn_pady = (0, 5)
        self.btn_ok = ttk.Button(frame, 
                            text='OK',
                            width=6,
                            bootstyle=PRIMARY,
                            command=self.on_ok)
        self.btn_ok.pack(side=RIGHT, padx=btn_padx, pady=btn_pady)
        self.btn_ok.focus_set()

        self.btn_cancel = ttk.Button(frame, 
                                text='Cancel',
                                width=6,
                                bootstyle=SECONDARY,
                                command=self.on_cancel)
        self.btn_cancel.pack(side=RIGHT, padx=btn_padx, pady=btn_pady)

    def on_cancel(self, event=None):
        self._result = None
        self.close()

    @abstractmethod
    def on_ok(self, event=None):
        ...

    @abstractmethod
    def on_changes(self):
        ...

    def _place_widget(self, master, widget, title: str|None=None):
        row = self.get_next_row()
        if title:
            ttk.Label(master, text=f'{title}:').grid(row=row, column=0, sticky=NW)

        widget.grid(row=row, column=1, sticky=EW, padx=self.custom_pad_x, pady=(self.custom_pad_y, 0))

    def _create_colour_select(self, master, title: str, variable, value: int):
        row = self.get_next_row()
        ttk.Label(master, text=f'{title}:').grid(row=row, column=0, sticky=EW)
        widget = ttk.Combobox(master,
                            textvariable=variable,
                            values=self.__get_colours(),
                            bootstyle=INFO)
        widget.current(newindex=value)
        widget['state'] = 'readonly'
        widget.grid(row=row, column=1, padx=self.custom_pad_x, sticky=EW)
        return widget

    def __get_colours(self):
        return [v.title() for v in ZXAttribute.COLOURS.keys()]

    @classmethod
    def _extract_attribute(cls, current: ZXAttribute|int|None) -> ZXAttribute:
        if current is None:
            return ZXAttribute.from_value(ZXToken.DEFAULT_ATTRIBUTE)
        return ZXAttribute.from_value(int(current))

    @classmethod
    def _extract_border(cls, border: ZXBorder|None=None) -> ZXBorder:
        if border is None:
            return ZXBorder.from_value(ZXToken.DEFAULT_BORDER)
        return ZXBorder.from_value(int(border))


class SelectAttributeDialog(BaseAttributeDialog):
    def __init__(self, master, title, current: ZXAttribute|None=None, border: ZXBorder|None=None, enable_preview: bool=True, enable_ink: bool=True, enable_paper: bool=True, enable_bright: bool=True, enable_flash: bool=True):
        super().__init__(master, title=title, current=current, border=border, enable_preview=enable_preview)
        self.enable_ink = enable_ink
        self.enable_paper = enable_paper
        self.enable_bright = enable_bright
        self.enable_flash = enable_flash

    def create_body(self, master):
        frame = super().create_body(master)
        self.var_ink = ttk.StringVar()
        self.var_paper = ttk.StringVar()
        self.var_bright = ttk.BooleanVar(value=self.attribute.is_bright)
        self.var_flash = ttk.BooleanVar(value=self.attribute.is_flashing)

        if self.enable_preview:
            self.lbl_preview = ttk.Label(frame)
            self._place_widget(frame, self.lbl_preview, 'Preview')
        if self.enable_ink:
            self.btn_ink = self._create_colour_select(frame, 'Ink', self.var_ink, self.attribute.ink)
            self.btn_ink.bind('<<ComboboxSelected>>', self.__on_update_ink)
        if self.enable_paper:
            self.btn_paper = self._create_colour_select(frame, 'Paper', self.var_paper, self.attribute.paper)
            self.btn_paper.bind('<<ComboboxSelected>>', self.__on_update_paper)
        if self.enable_bright:
            self._place_widget(
                frame,
                ttk.Checkbutton(frame, 
                                text='Bright', 
                                variable=self.var_bright,
                                command=self.__on_update_bright,
                                bootstyle='square toggle'))
        if self.enable_flash:
            self._place_widget(
                frame,
                ttk.Checkbutton(frame, 
                                text='Flashing', 
                                variable=self.var_flash, 
                                command=self.__on_update_flash,
                                bootstyle='square toggle'))

        ttk.Separator(master).pack(fill=X, expand=True, pady=self.custom_pad_y)
        self.on_changes()
        return frame

    def __on_update_ink(self, event=None):
        self.attribute.ink = self.btn_ink.current()
        self.on_changes()

    def __on_update_paper(self, event=None):
        self.attribute.paper = self.btn_paper.current()
        self.on_changes()

    def __on_update_bright(self, event=None):
        self.attribute.is_bright = self.var_bright.get()
        self.on_changes()

    def __on_update_flash(self, event=None):
        self.attribute.is_flashing = self.var_flash.get()
        self.on_changes()

    def on_ok(self, event=None):
        self._result = self.attribute
        self.close()

    def on_changes(self):
        if self.enable_preview:
            self.preview.refresh(self, self.lbl_preview)

    @classmethod
    def prompt_value(cls, master, title: str, current: ZXAttribute|None=None, border: ZXBorder|None=None, enable_preview: bool=True, enable_ink: bool=True, enable_paper: bool=True, enable_bright: bool=True, enable_flash: bool=True) -> typing.Any:
        dialog = cls(master, 
                     title=title, 
                     current=current,
                     border=border,
                     enable_preview=enable_preview,
                     enable_ink=enable_ink,
                     enable_paper=enable_paper,
                     enable_bright=enable_bright,
                     enable_flash=enable_flash)
        dialog.show(wait_for_result=True)
        return dialog.result


class SelectBorderDialog(BaseAttributeDialog):
    def __init__(self, master, title, current: ZXAttribute|None=None, border: ZXBorder|None=None, enable_preview: bool=True):
        super().__init__(master, title=title, current=current, border=border, enable_preview=enable_preview)

    def create_body(self, master):
        frame = super().create_body(master)
        self.var_border = ttk.StringVar()
        self.var_enabled = ttk.BooleanVar(value=self.border.is_enabled)

        if self.enable_preview:
            self.lbl_preview = ttk.Label(frame)
            self._place_widget(frame, self.lbl_preview, 'Preview')
        self.btn_border = self._create_colour_select(frame, 'Border', self.var_border, self.border.border)
        self.btn_border.bind('<<ComboboxSelected>>', self.__on_update_border)
        self._place_widget(
            frame,
            ttk.Checkbutton(frame, 
                            text='Enabled', 
                            variable=self.var_enabled,
                            command=self.__on_update_enabled,
                            bootstyle='square toggle'))

        ttk.Separator(master).pack(fill=X, expand=True, pady=self.custom_pad_y)
        self.on_changes()
        return frame

    def __on_update_border(self, event=None):
        self.border.border = self.btn_border.current()
        if not self.var_enabled.get():
            self.border.is_enabled = True
            self.var_enabled.set(True)
        self.on_changes()

    def __on_update_enabled(self, event=None):
        self.border.is_enabled = self.var_enabled.get()
        self.on_changes()

    def on_ok(self, event=None):
        self._result = self.border
        self.close()

    def on_changes(self):
        if self.enable_preview:
            self.preview.refresh(self, self.lbl_preview)


    @classmethod
    def prompt_value(cls, master, title: str, current: ZXAttribute|None=None, border: ZXBorder|None=None, enable_preview: bool=True) -> typing.Any:
        dialog = cls(master, 
                     title=title, 
                     current=current,
                     border=border,
                     enable_preview=enable_preview)
        dialog.show(wait_for_result=True)
        return dialog.result



class AttributePreview:
    DEFAULT_FILL = 0xff
    NUM_LINES = 6
    BORDER_FILL = 0x8f
    'ASCII-value for a filled block'

    def __init__(self, dialog: BaseAttributeDialog):
        self.scale_value = 2
        self.zx_token = self.__create_token(dialog)

    def refresh(self, dialog: BaseAttributeDialog, label: ttk.Label):
        for char_x in range(1, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            for char_y in range(1, self.NUM_LINES):
                self.zx_token.set_attribute(char_x, char_y, char_attribute=int(dialog.attribute))

        border_attribute = dialog.border.get_border()
        for i in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.zx_token.set_cell(i, 0, char_code=self.BORDER_FILL, char_attribute=border_attribute)
            self.zx_token.set_cell(i, self.NUM_LINES - 1, char_code=self.BORDER_FILL, char_attribute=border_attribute)
        for i in range(0, self.NUM_LINES + 1):
            self.zx_token.set_cell(0, i, char_code=self.BORDER_FILL, char_attribute=border_attribute)
            self.zx_token.set_cell(31, i, char_code=self.BORDER_FILL, char_attribute=border_attribute)
        
        self.__flip_to(label)


    def __flip_to(self, label: ttk.Label):
        pil_img = Image.fromarray(self.__get_rgb())
        tk_img = ImageTk.PhotoImage(pil_img)
        label.config(image=tk_img)
        self.image = tk_img

    def __get_rgb(self):
        rgb_data = self.zx_token.to_rgb()

        # Conveniently forget everything after line 10
        rgb_data = rgb_data[0:(self.NUM_LINES*8)]

        if not self.scale_value == 1:
            return numpy.repeat(numpy.repeat(rgb_data, self.scale_value, axis=0), self.scale_value, axis=1)
        return rgb_data

    def __create_token(self, dialog: BaseAttributeDialog) -> ZXToken:
        doc = ZXToken(init_attribute=int(dialog.attribute))
        x = 1
        y = 1
        for char_code, data in doc.font.symbols():
            doc.set_cell(x, y, char_code=char_code)
            x += 1
            if x >= 31:
                x = 1
                y += 1

        # Fill out remaining line cells
        for x in range(x, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            doc.set_cell(x, y, char_code=ZXFont.ASCII_SPACE)
        return doc
