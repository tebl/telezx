import numpy, typing
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Dialog
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from .. import ZXAttribute, ZXToken, ZXFont
from .custom_dialog import CustomDialog

class SelectAttributeDialog(CustomDialog):
    def __init__(self, master, title, current: ZXAttribute=None):
        super().__init__(master, title=title)
        self.attribute = ZXAttribute.from_value(int(current) if current else ZXToken.DEFAULT_ATTRIBUTE)
        self.next_row = 0

    def create_body(self, master):
        frame = super().create_body(master)
        self.var_ink = ttk.StringVar()
        self.var_paper = ttk.StringVar()
        self.var_bright = ttk.BooleanVar(value=self.attribute.is_bright)
        self.var_flash = ttk.BooleanVar(value=self.attribute.is_flashing)

        self.lbl_preview = ttk.Label(frame)
        self.preview = AttributePreview(self.lbl_preview, self.attribute)
        self.__place_widget(frame, self.lbl_preview, 'Preview')

        self.btn_ink = self.__create_colour_select(frame, 'Ink', self.var_ink, self.attribute.ink)
        self.btn_ink.bind('<<ComboboxSelected>>', self.__on_update_ink)
        self.btn_paper = self.__create_colour_select(frame, 'Paper', self.var_paper, self.attribute.paper)
        self.btn_paper.bind('<<ComboboxSelected>>', self.__on_update_paper)
        self.__place_widget(
            frame,
            ttk.Checkbutton(frame, 
                            text='Bright', 
                            variable=self.var_bright,
                            command=self.__on_update_bright,
                            bootstyle='square toggle'))
        self.__place_widget(
            frame,
            ttk.Checkbutton(frame, 
                            text='Flashing', 
                            variable=self.var_flash, 
                            command=self.__on_update_flash,
                            bootstyle='square toggle'))

        ttk.Separator(master).pack(fill=X, expand=True, pady=self.custom_pad_y)
        return frame

    def __place_widget(self, master, widget, title: str|None=None):
        if title:
            ttk.Label(master, text=f'{title}:').grid(row=self.next_row, column=0, sticky=NW)

        widget.grid(row=self.next_row, column=1, sticky=EW, padx=self.custom_pad_x, pady=(self.custom_pad_y, 0))
        self.next_row += 1

    def __create_colour_select(self, master, title: str, variable, value: int):
        ttk.Label(master, text=f'{title}:').grid(row=self.next_row, column=0, sticky=EW)
        widget = ttk.Combobox(master,
                            textvariable=variable,
                            values=self.__get_colours(),
                            bootstyle=INFO)
        widget.current(newindex=value)
        widget['state'] = 'readonly'
        widget.grid(row=self.next_row, column=1, padx=self.custom_pad_x, sticky=EW)
        self.next_row += 1
        return widget

    def __get_colours(self):
        return [v.title() for v in ZXAttribute.COLOURS.keys()]

    def __on_update_ink(self, event=None):
        self.attribute.ink = self.btn_ink.current()
        self.__on_changes()

    def __on_update_paper(self, event=None):
        self.attribute.paper = self.btn_paper.current()
        self.__on_changes()

    def __on_update_bright(self, event=None):
        self.attribute.is_bright = self.var_bright.get()
        self.__on_changes()

    def __on_update_flash(self, event=None):
        self.attribute.is_flashing = self.var_flash.get()
        self.__on_changes()

    def __on_changes(self):
        self.preview.refresh()

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

    def on_ok(self, event=None):
        self._result = self.attribute
        self.close()

    @classmethod
    def get_result(cls, master, title: str, current: ZXAttribute|None=None) -> typing.Any:
        dialog = cls(master, 
                     title=title, 
                     current=current)
        dialog.show(wait_for_result=True)
        return dialog.result


class AttributePreview:
    DEFAULT_FILL = 0xff

    def __init__(self, label: ttk.Label, attribute: ZXAttribute):
        self.scale_value = 2
        self.label = label
        self.attribute = attribute
        self.zx_token = self.__create_token()
        self.__flip_canvas()

    def refresh(self):
        self.zx_token.zx_screen.memory[self.zx_token.zx_screen.SIZE_DATA:] = int(self.attribute)
        self.__flip_canvas()

    def __flip_canvas(self):
        pil_img = Image.fromarray(self.__get_rgb())
        tk_img = ImageTk.PhotoImage(pil_img)
        self.label.config(image=tk_img)
        self.image = tk_img

    def __get_rgb(self):
        rgb_data = self.zx_token.to_rgb()

        # Forget everything after line 10
        rgb_data = rgb_data[0:(10*8)]

        if not self.scale_value == 1:
            return numpy.repeat(numpy.repeat(rgb_data, self.scale_value, axis=0), self.scale_value, axis=1)
        return rgb_data

    def __create_token(self) -> ZXToken:
        doc = ZXToken(init_attribute=self.attribute)
        x = 1
        y = 1
        for char_code, data in doc.font.symbols():
            doc.set_cell(x, y, char_code=char_code)
            x += 1
            if x >= 30:
                x = 1
                y += 1

        x = 1
        y += 2
        for char_code, data in doc.glyph.symbols():
            doc.set_cell(x, y, char_code=char_code)
            x += 1
            if x >= 30:
                x = 1
                y += 1
        return doc
