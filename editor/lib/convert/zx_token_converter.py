from pathlib import Path
from .base_converter import BaseConverter
from .. import ZXToken, ZXDocument

class ZXTokenConverter(BaseConverter):
    zx_token: ZXToken

    def __init__(self, zx_token: ZXToken):
        super().__init__()
        self.zx_token = zx_token

    def save_as(self, output_path: Path) -> bool:
        previous_path = self.zx_token.document_path
        self.zx_token.set_document(output_path)
        self.zx_token.save()
        self.zx_token.set_document(previous_path)
        return True

    def export_to(self, output_path: Path) -> bool:
        if not output_path.suffix in self.get_export_suffixes():
            raise RuntimeError(f'Unknown suffix - {output_path.suffix}')
        match output_path.suffix:
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

    @classmethod
    def get_format_suffix(cls) -> str:
        return ZXToken.FILE_EXTENSION

    @classmethod
    def get_export_suffixes(cls, strip_period=False) -> str:
        return [ v[1:] if strip_period else v for v in [ZXToken.FILE_EXTENSION,
                                                        ZXDocument.EXTENSION_TOKEN,
                                                        '.png', 
                                                        '.bmp', 
                                                        '.jpg', 
                                                        '.tif',
                                                        '.scr']]