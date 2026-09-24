from pathlib import Path
from .base_converter import BaseConverter
from .. import ZXToken, ZXDocument

class TKNConverter(BaseConverter):
    @classmethod
    def export_to(cls, zx_token: ZXToken, output_path: Path) -> bool:
        zx_token.export_to_specscii(output_path)
        return True

    @classmethod
    def get_format_suffix(cls) -> str:
        return ZXDocument.EXTENSION_TOKEN