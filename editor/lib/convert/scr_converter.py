from pathlib import Path
from .base_converter import BaseConverter
from .zx_token_converter import ZXTokenConverter
from .. import ZXToken, ZXDocument

class SCRConverter(BaseConverter):
    @classmethod
    def import_from(cls, input_file: Path) -> ZXTokenConverter:
        cls.info(f'Import SCR from {input_file.name}', indent=0)
        doc = ZXToken()
        doc.set_background(background_path=input_file)
        return ZXTokenConverter(doc)

    @classmethod
    def get_format_suffix(cls) -> str:
        return ZXDocument.EXTENSION_SCR