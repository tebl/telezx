from abc import ABC, abstractmethod
from pathlib import Path

class BaseDocument(ABC):
    def __init__(self, debug_enabled: bool=False):
        self.debug_enabled: bool=debug_enabled
        self._changes: bool=False
        self.document_path: Path|None=None

    def get_title(self) -> str:
        parts = ['*'] if self.has_changes() else []
        if self.is_untitled():
            parts.append('Untitled')
        else:
            parts.append(self.document_path)
        return ''.join(parts)

    def set_file(self, document_path: Path):
        self.document_path = document_path

    def has_changes(self) -> bool:
        return self._changes

    def is_untitled(self):
        return True if self.document_path == None else False

    @abstractmethod
    def load(self, document_path: Path) -> bool:
        ...

    @classmethod
    @abstractmethod
    def create(cls, document_path: Path):
        return cls()

    @classmethod
    def from_file(cls, document_path: Path):
        doc = cls.create(document_path)
        doc.load(document_path)
        return doc
