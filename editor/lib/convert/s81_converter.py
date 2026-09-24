import typing
from pathlib import Path
from .base_converter import BaseConverter
from .zx_token_converter import ZXTokenConverter
from .. import ZXScreen, ZXScreenIterator, ZXFont, ZXToken

class S81Converter(BaseConverter):
    ATTRIBUTE = ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.WHITE)
    ATTRIBUTE_ALT = ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK)
    CHARACTER_SET = {
        0x00: (ord(' '), ATTRIBUTE),
        0x01: (130, ATTRIBUTE),
        0x02: (129, ATTRIBUTE),
        0x03: (131, ATTRIBUTE),
        0x04: (136, ATTRIBUTE),
        0x05: (138, ATTRIBUTE),
        0x06: (137, ATTRIBUTE),
        0x07: (139, ATTRIBUTE),
        0x08: (144, ATTRIBUTE),
        0x09: (146, ATTRIBUTE),
        0x0a: (145, ATTRIBUTE),
        0x0b: (34, ATTRIBUTE),          # "
        0x0c: (96, ATTRIBUTE),          # £
        0x0d: (ord('$'), ATTRIBUTE),
        0x0e: (ord(':'), ATTRIBUTE),
        0x0f: (ord('?'), ATTRIBUTE),
        0x10: (ord('('), ATTRIBUTE),
        0x11: (ord(')'), ATTRIBUTE),
        0x12: (ord('>'), ATTRIBUTE),
        0x13: (ord('<'), ATTRIBUTE),
        0x14: (ord('='), ATTRIBUTE),
        0x15: (ord('+'), ATTRIBUTE),
        0x16: (ord('-'), ATTRIBUTE),
        0x17: (ord('*'), ATTRIBUTE),
        0x18: (ord('/'), ATTRIBUTE),
        0x19: (ord(';'), ATTRIBUTE),
        0x1a: (ord(','), ATTRIBUTE),
        0x1b: (ord('.'), ATTRIBUTE),
        0x1c: (ord('0'), ATTRIBUTE),
        0x1d: (ord('1'), ATTRIBUTE),
        0x1e: (ord('2'), ATTRIBUTE),
        0x1f: (ord('3'), ATTRIBUTE),
        0x20: (ord('4'), ATTRIBUTE),
        0x21: (ord('5'), ATTRIBUTE),
        0x22: (ord('6'), ATTRIBUTE),
        0x23: (ord('7'), ATTRIBUTE),
        0x24: (ord('8'), ATTRIBUTE),
        0x25: (ord('9'), ATTRIBUTE),
        0x26: (ord('A'), ATTRIBUTE),
        0x27: (ord('B'), ATTRIBUTE),
        0x28: (ord('C'), ATTRIBUTE),
        0x29: (ord('D'), ATTRIBUTE),
        0x2a: (ord('E'), ATTRIBUTE),
        0x2b: (ord('F'), ATTRIBUTE),
        0x2c: (ord('G'), ATTRIBUTE),
        0x2d: (ord('H'), ATTRIBUTE),
        0x2e: (ord('I'), ATTRIBUTE),
        0x2f: (ord('J'), ATTRIBUTE),
        0x30: (ord('K'), ATTRIBUTE),
        0x31: (ord('L'), ATTRIBUTE),
        0x32: (ord('M'), ATTRIBUTE),
        0x33: (ord('N'), ATTRIBUTE),
        0x34: (ord('O'), ATTRIBUTE),
        0x35: (ord('P'), ATTRIBUTE),
        0x36: (ord('Q'), ATTRIBUTE),
        0x37: (ord('R'), ATTRIBUTE),
        0x38: (ord('S'), ATTRIBUTE),
        0x39: (ord('T'), ATTRIBUTE),
        0x3a: (ord('U'), ATTRIBUTE),
        0x3b: (ord('V'), ATTRIBUTE),
        0x3c: (ord('W'), ATTRIBUTE),
        0x3d: (ord('X'), ATTRIBUTE),
        0x3e: (ord('Y'), ATTRIBUTE),
        0x3f: (ord('Z'), ATTRIBUTE),
        0x80: (ord(' '), ATTRIBUTE_ALT),
        0x81: (130, ATTRIBUTE_ALT),
        0x82: (129, ATTRIBUTE_ALT),
        0x83: (131, ATTRIBUTE_ALT),
        0x84: (136, ATTRIBUTE_ALT),
        0x85: (138, ATTRIBUTE_ALT),
        0x86: (137, ATTRIBUTE_ALT),
        0x87: (139, ATTRIBUTE_ALT),
        0x88: (144, ATTRIBUTE_ALT),
        0x89: (146, ATTRIBUTE_ALT),
        0x8a: (145, ATTRIBUTE_ALT),
        0x8b: (34, ATTRIBUTE_ALT),          # "
        0x8c: (96, ATTRIBUTE_ALT),          # £
        0x8d: (ord('$'), ATTRIBUTE_ALT),
        0x8e: (ord(':'), ATTRIBUTE_ALT),
        0x8f: (ord('?'), ATTRIBUTE_ALT),
        0x90: (ord('('), ATTRIBUTE_ALT),
        0x91: (ord(')'), ATTRIBUTE_ALT),
        0x92: (ord('>'), ATTRIBUTE_ALT),
        0x93: (ord('<'), ATTRIBUTE_ALT),
        0x94: (ord('='), ATTRIBUTE_ALT),
        0x95: (ord('+'), ATTRIBUTE_ALT),
        0x96: (ord('-'), ATTRIBUTE_ALT),
        0x97: (ord('*'), ATTRIBUTE_ALT),
        0x98: (ord('/'), ATTRIBUTE_ALT),
        0x99: (ord(';'), ATTRIBUTE_ALT),
        0x9a: (ord(','), ATTRIBUTE_ALT),
        0x9b: (ord('.'), ATTRIBUTE_ALT),
        0x9c: (ord('0'), ATTRIBUTE_ALT),
        0x9d: (ord('1'), ATTRIBUTE_ALT),
        0x9e: (ord('2'), ATTRIBUTE_ALT),
        0x9f: (ord('3'), ATTRIBUTE_ALT),
        0xa0: (ord('4'), ATTRIBUTE_ALT),
        0xa1: (ord('5'), ATTRIBUTE_ALT),
        0xa2: (ord('6'), ATTRIBUTE_ALT),
        0xa3: (ord('7'), ATTRIBUTE_ALT),
        0xa4: (ord('8'), ATTRIBUTE_ALT),
        0xa5: (ord('9'), ATTRIBUTE_ALT),
        0xa6: (ord('A'), ATTRIBUTE_ALT),
        0xa7: (ord('B'), ATTRIBUTE_ALT),
        0xa8: (ord('C'), ATTRIBUTE_ALT),
        0xa9: (ord('D'), ATTRIBUTE_ALT),
        0xaa: (ord('E'), ATTRIBUTE_ALT),
        0xab: (ord('F'), ATTRIBUTE_ALT),
        0xac: (ord('G'), ATTRIBUTE_ALT),
        0xad: (ord('H'), ATTRIBUTE_ALT),
        0xae: (ord('I'), ATTRIBUTE_ALT),
        0xaf: (ord('J'), ATTRIBUTE_ALT),
        0xb0: (ord('K'), ATTRIBUTE_ALT),
        0xb1: (ord('L'), ATTRIBUTE_ALT),
        0xb2: (ord('M'), ATTRIBUTE_ALT),
        0xb3: (ord('N'), ATTRIBUTE_ALT),
        0xb4: (ord('O'), ATTRIBUTE_ALT),
        0xb5: (ord('P'), ATTRIBUTE_ALT),
        0xb6: (ord('Q'), ATTRIBUTE_ALT),
        0xb7: (ord('R'), ATTRIBUTE_ALT),
        0xb8: (ord('S'), ATTRIBUTE_ALT),
        0xb9: (ord('T'), ATTRIBUTE_ALT),
        0xba: (ord('U'), ATTRIBUTE_ALT),
        0xbb: (ord('V'), ATTRIBUTE_ALT),
        0xbc: (ord('W'), ATTRIBUTE_ALT),
        0xbd: (ord('X'), ATTRIBUTE_ALT),
        0xbe: (ord('Y'), ATTRIBUTE_ALT),
        0xbf: (ord('Z'), ATTRIBUTE_ALT)
    }

    @classmethod
    def import_from(cls, input_file: Path) -> ZXTokenConverter:
        cls.info(f'Import s81 from {input_file.name}', indent=0)
        non_convertable = 0
        token = ZXToken(init_attribute=S81Converter.ATTRIBUTE)
        with open(input_file, 'rb') as file:
            for char_x, char_y in ZXScreenIterator(0, 0, False):
                char_code = ord(file.read(1))
                char_attribute = cls.ATTRIBUTE
                if char_code in cls.CHARACTER_SET:
                    char_code, char_attribute = cls.CHARACTER_SET[char_code]
                else:
                    char_code = ZXFont.ASCII_SPACE
                    non_convertable += 1

                token.set_cell(char_x, char_y, char_code=char_code, char_attribute=char_attribute)

            remaining = len(file.read())
            if remaining:
                cls.error(f'{remaining} bytes left in file (probably not 53c formatted file)!')
                raise RuntimeError('Does not appear to be 53c formatted file')
        if non_convertable:
            cls.warning(f'{non_convertable} characters could not be mapped')
        return ZXTokenConverter(token)

    @classmethod
    def get_format_suffix(cls) -> str:
        return '.s81'