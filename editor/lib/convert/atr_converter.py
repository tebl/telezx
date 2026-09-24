import typing
from pathlib import Path
from .base_converter import BaseConverter
from .. import ZXScreen, ZXScreenIterator, ZXFont, ZXToken

class ATRConverter(BaseConverter):
    BLENDED = 0b10000000
    'Replaces the blinking bit'
    BLENDED_CHAR_CODE = 144
    'Custom alternating bit pattern in font_glyphs (added for TeleZX)'

    @classmethod
    def import_from(cls, input_file: Path) -> ZXToken:
        cls.info(f'Import 53c data from {input_file.name}', indent=0)
        token = ZXToken(init_attribute=ZXToken.DEFAULT_ATTRIBUTE)
        with open(input_file, 'rb') as file:
            for char_x, char_y in ZXScreenIterator(0, 0, False):
                data = ord(file.read(1))
                parsed = cls.to_parsed_attribute(data)

                token.set_cell(char_x, char_y,
                               char_code=(ZXFont.ASCII_SPACE if parsed['is_blended'] else cls.BLENDED_CHAR_CODE),
                               char_attribute=ZXScreen.to_attribute(ink=parsed['ink'], paper=parsed['paper'], is_bright=parsed['is_bright']))
            remaining = len(file.read())
            if remaining:
                cls.error(f'{remaining} bytes left in file (probably not 53c formatted file)!')
                raise RuntimeError('Does not appear to be 53c formatted file')
        return token

    @classmethod
    def to_parsed_attribute(cls, attribute) -> dict[str, typing.Any]:
        return {
            'is_blended': bool((attribute & cls.BLENDED) == cls.BLENDED),
            'is_bright': bool((attribute & ZXScreen.BRIGHT) == ZXScreen.BRIGHT),
            'paper': (attribute & 0b00111000) >> 3,
            'ink': attribute & 0b00000111
        }

    @classmethod
    def get_format_suffix(cls) -> str:
        return '.atr'