from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .. import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class RepositoryHelper:
    repository: Path
    src_path: Path
    out_path: Path

    DEFAULT_REPOSITORY = 'telezx'

    def __init__(self, repository: Path):
        self.logger = ZXLogger.get_instance()
        self.repository = Path(repository)
        self.src_path = self.repository / 'src'
        self.out_path = self.repository / 'out'
        self.registry_path = self.repository / 'src' / f'{self.DEFAULT_REPOSITORY}{ZXRegistry.FILE_EXTENSION}'

    def create_path_structure(self, exist_ok=True) -> bool:
        self.src_path.mkdir(exist_ok=exist_ok)
        self.out_path.mkdir(exist_ok=exist_ok)
        return True

    def generate_document_path(self, document_id, path_hint=None):
        base_path = self.src_path / utilities.suggest_document_path(document_id, path_hint)
        return base_path / "{}{}".format(
            utilities.format_padded_id(document_id),
            ZXDocument.EXTENSION_DOCUMENT
        )

    def open_registry(self) -> ZXRegistry:
        self.registry = ZXRegistry.from_file(self.registry_path, allow_create=True)
        return self.registry