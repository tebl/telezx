import yaml, typing
from abc import ABC, abstractmethod
from pathlib import Path

from . import utilities
from .zx_logger import ZXLogger

class BaseDocument(ABC):
    def __init__(self, debug_enabled: bool=False):
        self.debug_enabled: bool=debug_enabled
        self._changes: bool=False
        self._document_path: Path|None=None

    @property
    def document_path(self) -> Path:
        return self._document_path

    @document_path.setter
    def document_path(self, document_path: Path):
        self._document_path = document_path

    def get_title(self) -> str:
        parts = ['*'] if self.has_changes() else []
        if self.is_untitled():
            parts.append('Untitled')
        else:
            parts.append(self._document_path)
        return ''.join(parts)

    def has_changes(self) -> bool:
        return self._changes

    def is_untitled(self):
        return True if self._document_path == None else False

    def save(self) -> bool:
        if not self.document_path:
            raise Exception('No document set')
        with open(self.document_path, 'w') as file:
            yaml.dump(
                self.to_dict(), 
                file, 
                indent=4, 
                default_flow_style=False, 
                sort_keys=True
            )
        self._changes = False
        return True

    @abstractmethod
    def to_dict(self):
        ...

    @classmethod
    @abstractmethod
    def _yaml_defaults(cls):
        return {cls.__name__: {}}

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Any:
        '''
        Create object from the supplied dictionary. Parent implementation will
        apply basic structure validation, and will return the expected root
        node found within the data structure.
        '''
        if not len(data) == 1:
            raise ValueError("expected one key specifying datatype, found {}".format(len(data)))
        if cls.__name__ not in data:
            raise ValueError("does not look like a {}-file".format(cls.__name__))
        return data[cls.__name__]

    @classmethod
    def from_file(cls, document_path: Path) -> typing.Self:
        ZXLogger.get_instance().debug('Loading document from', document_path)
        data = cls._yaml_defaults()
        data = utilities.update_tree(data, cls._get_yaml(document_path))

        doc: typing.Self = cls.from_dict(data)
        doc.document_path = document_path
        return doc

    @classmethod
    def _get_yaml(cls, yaml_path) -> dict[str, typing.Any]:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            if data is None or cls.__name__ not in data:
                raise ValueError("does not look like a {}-file".format(cls.__name__))
            return data