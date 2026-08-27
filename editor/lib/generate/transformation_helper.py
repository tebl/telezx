import numpy
from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .document_helper import DocumentHelper
from .. import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class TransformationHelper(DocumentHelper):
    def __init__(self, repository: Path):
        super().__init__(repository)
        self.scr_path = None
        self.zx_screen = None

    def clear_line(self, char_y: int):
        self.__ensure_loaded()
        print('clear_line')

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

    def __get_backup_path(self) -> Path:
        return self.scr_path.with_suffix(ZXDocument.EXTENSION_SCR_ORIGINAL)

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