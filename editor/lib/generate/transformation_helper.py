import numpy
from pathlib import Path
from PIL import Image
from .document_helper import DocumentHelper
from .. import ZXFont, ZXGlyph, ZXScreen, ZXScreenIterator, ZXDocument, ZXToken, ZXPage, ZXPage_Overlay, utilities

class TransformationHelper(DocumentHelper):
    src_path: Path
    zx_screen: ZXScreen

    def __init__(self, repository: Path):
        super().__init__(repository)
        self.scr_path = None
        self.zx_screen = None

    def create_preview(self):
        self.__ensure_loaded(create_backup=False)
        path_out = self.__get_preview_path()
        legend_offset = ZXFont.GLYPH_WIDTH*2

        legend = ZXScreen()
        legend.clear_memory(set_attribute=ZXScreen.to_attribute(is_bright=True, ink=ZXScreen.BLACK, paper=ZXScreen.WHITE))
        font = ZXFont.get_default(generate_rgb=True)
        font_alt = ZXFont.get_default(generate_rgb=True, rgb_fg=[160, 160, 160])

        pixels = numpy.zeros(shape=(ZXScreen.SCREEN_HEIGHT_PIXELS + legend_offset, ZXScreen.SCREEN_WIDTH_PIXELS + legend_offset, 3), dtype=numpy.uint8)
        pixels[legend_offset:, legend_offset:] = self.zx_screen.to_rgb()

        for char_x in range(0, ZXScreen.SCREEN_WIDTH_CHARS):
            padded = utilities.format_padded_int(char_x)

            start_y = 0
            end_y = start_y + ZXFont.GLYPH_HEIGHT

            start_x = legend_offset + (char_x * ZXFont.GLYPH_WIDTH)
            end_x = start_x + ZXFont.GLYPH_WIDTH

            using_font = font if (char_x % 2) else font_alt
            pixels[start_y:end_y, start_x:end_x] = using_font.get_ascii(padded[0], rgb=True)
            pixels[start_y+ZXFont.GLYPH_HEIGHT:end_y+ZXFont.GLYPH_HEIGHT, start_x:end_x] = using_font.get_ascii(padded[1], rgb=True)

        for char_y in range(0, ZXScreen.SCREEN_HEIGHT_CHARS):
            padded = utilities.format_padded_int(char_y)

            start_y = legend_offset + (char_y * ZXFont.GLYPH_HEIGHT)
            end_y = start_y + ZXFont.GLYPH_HEIGHT

            start_x = 0
            end_x = start_x + ZXFont.GLYPH_WIDTH

            using_font = font if (char_y % 2) else font_alt
            pixels[start_y:end_y, start_x:end_x] = using_font.get_ascii(padded[0], rgb=True)
            pixels[start_y:end_y, start_x+ZXFont.GLYPH_WIDTH:end_x+ZXFont.GLYPH_WIDTH] = using_font.get_ascii(padded[1], rgb=True)

        image = Image.fromarray(pixels)
        image.save(path_out)
        self.logger.info('Created preview', path_out)

    def __plot_character(self, pixels: numpy.ndarray):
        pass

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
        self.zx_screen.write_cell(char_x, char_y, ZXGlyph.generate_blank_glyph(), self.__get_attribute(attribute))
        return True

    def transform_clear_line(self, char_y: int, attribute: int|None=None) -> bool:
        self.__ensure_loaded()
        attribute = self.__get_attribute(attribute)
        self.logger.info('Clearing line', char_y)
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.zx_screen.write_cell(char_x, char_y, ZXGlyph.generate_blank_glyph(), attribute)
        return True

    def transform_delete_line(self, char_y: int, attribute: int|None=None) -> bool:
        self.__ensure_loaded()
        self.logger.info('Deleting line', char_y)
        self.transform_scroll(delta_x=0, delta_y=-1, start_y=char_y)
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.zx_screen.write_cell(char_x, ZXScreen.SCREEN_HEIGHT_CHARS - 1, ZXGlyph.generate_blank_glyph(), attribute)
        return True

    def transform_scroll(self, delta_x: int=0, delta_y: int=0, start_x: int=0, start_y: int=0) -> bool:
        if not delta_x == 0 and start_x == 0:
            self.logger.info('Scrolling', 'left' if delta_x < 0 else 'right', delta_x, 'characters')
        if not delta_y == 0 and start_y == 0:
            self.logger.info('Scrolling', 'up' if delta_y < 0 else 'down', delta_y, 'character lines')

        self.original = ZXScreen()
        self.original.flip_memory(self.zx_screen.memory)
        for char_x, char_y in ZXScreenIterator(start_x, start_y):
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

    def __ensure_loaded(self, create_backup: bool=True):
        if not self.zx_screen:
            raise TransformationError("ZXScreen not loaded!")
        if create_backup:
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