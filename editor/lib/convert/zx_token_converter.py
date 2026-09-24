import string, yaml
from pathlib import Path
from .base_converter import BaseConverter
from .. import ZXScreen, ZXToken, ZXDocument, ZXScreenIterator, utilities

class ZXTokenConverter(BaseConverter):
    EXTENSION_TXT  = '.txt'
    EXTENSION_YAML = '.yaml'
    zx_token: ZXToken

    def __init__(self, zx_token: ZXToken):
        super().__init__()
        self.zx_token = zx_token

    @classmethod
    def open(cls, input_file: Path) -> ZXTokenConverter:
        return ZXTokenConverter(ZXToken.from_file(input_file))

    def save_as(self, output_path: Path) -> bool:
        previous_path = self.zx_token.document_path
        self.zx_token.set_document(output_path)
        self.zx_token.save()
        self.zx_token.set_document(previous_path)
        return True

    def export_to(self, output_path: Path) -> bool:
        if not output_path.suffix in self.get_export_suffixes(include_period=True):
            raise RuntimeError(f'Unknown suffix - {output_path.suffix}')
        match output_path.suffix:
            case self.EXTENSION_TXT:
                self._log_export(output_path.suffix, output_path)
                self.export_to_txt(output_path)
            case self.EXTENSION_YAML:
                self._log_export(output_path.suffix, output_path)
                self.export_to_yaml(output_path)
            case ZXDocument.EXTENSION_SCR:
                self._log_export(output_path.suffix, output_path)
                self.zx_token.export_to_scr(output_path)
            case ZXToken.FILE_EXTENSION:
                self._log_export(output_path.suffix, output_path)
                self.save_as(output_path)
            case ZXDocument.EXTENSION_TOKEN:
                self._log_export(output_path.suffix, output_path)
                self.zx_token.export_to_specscii(output_path)
            case _:
                self._log_export(output_path.suffix, output_path)
                self.zx_token.export_screenshot(output_path)
        return True

    def export_to_txt(self, output_path: Path):
        non_printable = 0
        with open(output_path, 'w') as file:
            for char_x, char_y in ZXScreenIterator(0, 0, False):
                char_code = self.zx_token.get_character(char_x, char_y)
                if char_code >= 0 and chr(char_code) in string.printable:
                    file.write(chr(char_code))
                else:
                    non_printable += 1
                    file.write(' ')
                if char_x == (ZXScreen.SCREEN_WIDTH_CHARS - 1):
                    file.write('\n')
        if non_printable:
            self.warning(f'{non_printable} non-printable characters ignored')

    def export_to_yaml(self, output_path: Path):
        non_printable = 0

        lines = []
        for char_y in range(0, ZXScreen.SCREEN_HEIGHT_CHARS):
            lines.append([])
            for char_x in range(0, ZXScreen.SCREEN_WIDTH_CHARS):
                char_code = self.zx_token.get_character(char_x, char_y)
                if char_code >= 0 and chr(char_code) in string.printable:
                    lines[char_y].append(chr(char_code))
                else:
                    non_printable += 1
                    lines[char_y].append(' ')
        if non_printable:
            self.warning(f'{non_printable} non-printable characters ignored')

        with open(output_path, 'w') as file:
            yaml.dump(
                { 
                    'TextDocument' : {
                        'pages': {
                            'ZXPage_ClearText': {
                                'text_lines': [
                                    utilities.QuotedYAML(''.join(lines[char_y])) for char_y in range(0, ZXScreen.SCREEN_HEIGHT_CHARS)
                                ]
                            }
                        }
                    }
                }, 
                file, 
                indent=4, 
                default_flow_style=False, 
                sort_keys=True
            )

    @classmethod
    def get_format_suffix(cls) -> str:
        return ZXToken.FILE_EXTENSION

    @classmethod
    def get_export_suffixes(cls, include_period: bool=True, include_graphical: bool=True, include_text: bool=True) -> list[str]:
        extensions = []
        if include_graphical:
            extensions.append(ZXToken.FILE_EXTENSION)
            extensions.append(ZXDocument.EXTENSION_TOKEN)
            extensions.append('.png')
            extensions.append('.bmp')
            extensions.append('.jpg')
            extensions.append('.tif')
            extensions.append('.scr')
        if include_text:
            extensions.append('.txt')
            extensions.append('.yaml')
        return [ v[1:] if not include_period else v for v in extensions]