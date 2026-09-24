from pathlib import Path
from .base_converter import BaseConverter
from .. import ZXToken, ZXDocument

class ZXTokenConverter(BaseConverter):
    @classmethod
    def save_as(cls, zx_token: ZXToken, output_path: Path) -> bool:
        previous_path = zx_token.document_path
        zx_token.set_document(output_path)
        zx_token.save()
        zx_token.set_document(previous_path)
        return True

    @classmethod
    def export_to(cls, zx_token: ZXToken, output_path: Path) -> bool:
        if not output_path.suffix in cls.get_export_suffixes():
            raise RuntimeError(f'Unknown suffix - {output_path.suffix}')
        match output_path.suffix:
            case ZXDocument.EXTENSION_SCR:
                cls._log_export(output_path.suffix, output_path)
                zx_token.export_to_scr(output_path)
            case ZXToken.FILE_EXTENSION:
                cls._log_export(output_path.suffix, output_path)
                cls.save_as(zx_token, output_path)
            case ZXDocument.EXTENSION_TOKEN:
                cls._log_export(output_path.suffix, output_path)
                zx_token.export_to_specscii(output_path)
            case _:
                cls._log_export(output_path.suffix, output_path)
                zx_token.export_screenshot(output_path)
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