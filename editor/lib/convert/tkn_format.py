from pathlib import Path
from .base_format import BaseFormat
from .. import ZXScreen, ZXDocument, DocumentIdentifierIterator, ZXToken, ZXPage_Token, utilities, ZXRegistry, ZXRegistryEntry, ZXRegistryTag

class TKNFormat(BaseFormat):
    @classmethod
    def get_format_suffix(cls):
        return ZXToken.FILE_EXTENSION