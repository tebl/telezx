from pathlib import Path
from .base_format import BaseFormat
from .. import ZXScreen, ZXScreenIterator, ZXFont, ZXToken, ZXPage_Token, utilities, ZXRegistry, ZXRegistryEntry, ZXRegistryTag

class ATRFormat(BaseFormat):
    @classmethod
    def import_file(cls, input_file: Path) -> ZXToken:
        token = ZXToken(init_attribute=ZXToken.DEFAULT_ATTRIBUTE)
        with open(input_file, 'rb') as file:
            for char_x, char_y in ZXScreenIterator(0, 0, False):
                data = ord(file.read(1))
                parsed = cls.to_parsed_attribute(data)

                token.set_cell(char_x, char_y,
                               char_code=(ZXFont.ASCII_SPACE if parsed['is_blended'] else 144),
                               char_attribute=ZXScreen.to_attribute(ink=parsed['ink'], paper=parsed['paper'], is_bright=parsed['is_bright']))
                # print(data, parsed)
                # return token
            if len(file.read()):
                raise ValueError('Too many bytes')
        return token

    @classmethod
    def to_parsed_attribute(cls, attribute):
        return {
            'is_blended': bool((attribute & ZXScreen.FLASH) == ZXScreen.FLASH),
            'is_bright': bool((attribute & ZXScreen.BRIGHT) == ZXScreen.BRIGHT),
            'paper': (attribute & 0b00111000) >> 3,
            'ink': attribute & 0b00000111
        }

    @classmethod
    def get_format_suffix(cls):
        return '.atr'