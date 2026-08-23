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
        self.src_path = self.repository / ZXDocument.PATH_SRC
        self.asset_path = self.src_path / ZXDocument.PATH_ASSETS
        self.out_path = self.repository / ZXDocument.PATH_OUT
        self.registry_path = self.repository / 'src' / f'{self.DEFAULT_REPOSITORY}{ZXRegistry.FILE_EXTENSION}'

    def create_path_structure(self, exist_ok=True) -> bool:
        self.src_path.mkdir(exist_ok=exist_ok)
        self.out_path.mkdir(exist_ok=exist_ok)
        return True

    def generate_zx_token(self, page_path: Path, frame_path=None) -> ZXToken:
        if frame_path:
            return self.from_frame(frame_path, page_path)
        zx_token = ZXToken()
        zx_token.set_document(page_path)
        return zx_token

    def from_frame(self, frame_path: Path, page_path: Path) -> ZXToken:
        zx_token = ZXToken.from_file(frame_path)
        zx_token.set_document(page_path)
        return zx_token

    def resolve_frame_path(self, frame_name) -> Path:
        path = self.asset_path / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        if path.exists():
            return path
        path = utilities.get_project_root() / ZXDocument.PATH_ASSETS / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        if path.exists():
            return path
        raise FileNotFoundError(f'{frame_name} does not exist')

    def generate_document_path(self, document_id, path_hint=None) -> Path:
        base_path = self.src_path / utilities.suggest_document_path(document_id, path_hint)
        return base_path / "{}{}".format(
            utilities.format_padded_id(document_id),
            ZXDocument.EXTENSION_DOCUMENT
        )

    def generate_token_path(self, document: ZXDocument, page_id) -> Path:
        return document.working_path / "{}.{}{}".format(
            utilities.format_padded_id(document.document_id),
            utilities.format_padded_id(page_id, width=2),
            ZXToken.FILE_EXTENSION
        )

    def get_path_relative_to(self, document: ZXDocument, path: Path) -> Path:
        '''
        Transforms the supplied path so that it becomes relative to the
        document if it resides somewhere within the repository, if it doesn't
        then the path is resolved to the full path instead.
        '''
        path = path.resolve()
        if path.is_relative_to(self.repository):
            path = path.relative_to(document.working_path, walk_up=True)
        return path
    
    def open_registry(self) -> ZXRegistry:
        self.registry = ZXRegistry.from_file(self.registry_path, allow_create=True)
        return self.registry