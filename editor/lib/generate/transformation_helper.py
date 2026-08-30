import numpy
from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from PIL import Image
from .document_helper import DocumentHelper
from .. import ZXGlyph, ZXScreen, ZXScreenIterator, ZXDocument, ZXToken, ZXFrame, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class TransformationHelper(DocumentHelper):
    src_path: Path
    zx_screen: ZXScreen

    def __init__(self, repository: Path):
        super().__init__(repository)
        self.scr_path = None
        self.zx_screen = None

    def create_preview(self):
        self.__ensure_loaded()
        preview = self.__get_preview_path()

        image = Image.fromarray(self.zx_screen.to_rgb())
        image.save(preview)
        self.logger.info('Created preview', preview)

    def open_page(self, page: ZXPage) -> True:
        scr_path = self.__extract_path(page)
        self.open_scr(scr_path)
        return True

    def open_scr(self, scr_path: Path):
        if not scr_path.is_file():
            raise FileNotFoundError(scr_path)
        self.__open_scr(scr_path)

    def restore(self):
        self.__ensure_loaded()
        backup = self.__get_backup_path()
        if not backup.is_file():
            raise FileNotFoundError('No backup exists!')
        backup.copy(self.scr_path)
        self.__open_scr(self.scr_path)
        self.logger.info('Restore', backup.name, '->', self.scr_path.name)

    def save(self) -> bool:
        with open(self.scr_path, 'wb') as file:
            file.write(self.zx_screen.to_scr())
        return True

    def transform_clear_coordinate(self, char_x, char_y, attribute: int=None) -> bool:
        self.__ensure_loaded()
        self.logger.info('Clearing coordinate', f'(X={char_x}, Y={char_y})')
        self.zx_screen.write_cell(char_x, char_y, ZXGlyph.blank_glyph(), self.__get_attribute(attribute))
        return True

    def transform_clear_line(self, char_y: int, attribute: int|None=None) -> bool:
        self.__ensure_loaded()
        attribute = self.__get_attribute(attribute)
        self.logger.info('Clearing line', char_y)
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.zx_screen.write_cell(char_x, char_y, ZXGlyph.blank_glyph(), attribute)
        return True

    def transform_scroll(self, delta_x, delta_y) -> bool:
        if not delta_x == 0:
            self.logger.info('Scrolling', 'left' if delta_x < 0 else 'right', delta_x, 'characters')
        if not delta_y == 0:
            self.logger.info('Scrolling', 'up' if delta_y < 0 else 'down', delta_y, 'character lines')

        self.original = ZXScreen()
        self.original.flip_memory(self.zx_screen.memory)
        for char_x, char_y in ZXScreenIterator(0, 0):
            from_x = ((char_x - delta_x) % ZXScreen.SCREEN_WIDTH_CHARS)
            from_y = ((char_y - delta_y) % ZXScreen.SCREEN_HEIGHT_CHARS)

            self.zx_screen.write_cell(
                char_x, 
                char_y, 
                self.original.read_cell(from_x, from_y), 
                self.original.get_attribute_at(from_x, from_y))
        return True

    def __create_backup(self):
        backup = self.__get_backup_path()
        if not backup.is_file():
            self.logger.debug('Backup', self.scr_path.name, '->', backup.name)
            self.scr_path.copy(backup)

    def __ensure_loaded(self):
        if not self.zx_screen:
            raise TransformationError("ZXScreen not loaded!")
        self.__create_backup()

    def __extract_path(self, page: ZXPage) -> Path:
        if isinstance(page, ZXPage_Overlay):
            return page.scr_path
        raise TransformationFormatError(f'Page format {page.__class__.__name__} not supported!')

    def __get_attribute(self, attribute) -> int:
        if attribute is None:
            return ZXToken.DEFAULT_ATTRIBUTE
        return attribute

    def __get_backup_path(self) -> Path:
        return self.scr_path.with_suffix(ZXDocument.EXTENSION_SCR_ORIGINAL)

    def __get_preview_path(self) -> Path:
        return self.scr_path.with_suffix(ZXDocument.EXTENSION_SCR + ZXDocument.EXTENSION_SCREENSHOT)

    def __open_scr(self, scr_path: Path):
        self.scr_path = scr_path
        if not self.zx_screen:
            self.zx_screen = ZXScreen()
        self.zx_screen.flip_memory(numpy.fromfile(self.scr_path, dtype='uint8'))

class TransformationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class TransformationFormatError(TransformationError):
    def __init__(self, message: str):
        super().__init__(message)