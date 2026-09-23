from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .. import ZXDocument, ZXLogger, ZXRegistry, ZXScreen, ZXToken, utilities

class RepositoryHelper:
    repository: Path
    src_path: Path
    out_path: Path

    DEFAULT_REPOSITORY = 'telezx'

    def __init__(self, repository: Path):
        self.logger = ZXLogger.get_instance()
        self.repository = Path(repository)
        self.src_path = self.repository / ZXDocument.PATH_SRC
        self.asset_path = self.repository / ZXDocument.PATH_ASSETS
        self.out_path = self.repository / ZXDocument.PATH_OUT
        self.registry_path = self.repository / f'{self.DEFAULT_REPOSITORY}{ZXRegistry.FILE_EXTENSION}'

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

    def relative_path(self, path: Path) -> Path:
        return path.relative_to(utilities.get_project_root())

    def resolve_frame_path(self, frame_name: str) -> Path:
        path = self.asset_path / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        if path.exists():
            return path
        path = utilities.get_project_root() / ZXDocument.PATH_ASSETS / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        if path.exists():
            return path
        raise FileNotFoundError(f'{frame_name} does not exist')

    def generate_document_path(self, document_id: int, path_hint=None) -> Path:
        base_path = self.src_path / utilities.suggest_document_directory(document_id, path_hint)
        return base_path / ZXDocument.FILENAME_DEFAULT

    def generate_token_path(self, document: ZXDocument, asset_id: int, path_hint: str=None) -> Path:
        return self.generate_asset_path(document, asset_id, ZXToken.FILE_EXTENSION, path_hint)

    def generate_scr_path(self, document: ZXDocument, asset_id: int, path_hint: str=None) -> Path:
        return self.generate_asset_path(document, asset_id, ZXDocument.EXTENSION_SCR, path_hint)

    def generate_asset_path(self, document: ZXDocument, asset_id: int, extension: str, path_hint: str=None) -> Path:
        return document.working_path / utilities.suggest_asset_path(asset_id, extension, path_hint)

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

    def _create_document_path(self, document_id: int, path_hint: str, log_indent: int=0) -> Path:
        '''
        Create path for automatically created documents, wiping out any
        existing data if found.
        '''
        directory = self.src_path / utilities.suggest_document_directory(document_id, path_hint)
        if not directory.is_dir():
            directory.mkdir()
        else:
            self._clear_directory_assets(directory, log_indent)
        return directory

    def _clear_directory_assets(self, directory: Path, log_indent: int=0):
        '''
        Clears out assets found within the specified path, as a security
        precaution we'll only delete files starting with a two digit hex
        number - any other file will either be overwritten later, or they're
        assumed to have been left there interntionally.
        '''
        self.logger.debug('Clearing existing assets', indent=log_indent)
        for page_id in range(ZXDocument.ASSET_ID_MIN, ZXDocument.ASSET_ID_MAX + 1):
            asset_path = Path(directory) / utilities.suggest_asset_path(page_id, ZXToken.FILE_EXTENSION)
            if asset_path.is_file():
                self.logger.debug('Removing', asset_path, indent=(log_indent+1))
                asset_path.unlink()
            else:
                return

    def _get_document(self, document_id: int, description: str|None, abbreviation: str|None, target_directory: Path):
        return ZXDocument(
            self.repository,
            document_path=target_directory / ZXDocument.FILENAME_DEFAULT,
            document_id=document_id,
            description=description,
            abbreviation=abbreviation
        )

    def _get_page(self, document: ZXDocument, add_frame: bool=True) -> ZXToken:
        frame_name = 'default_frame' if add_frame else 'default'
        return self.from_frame(
            self.resolve_frame_path(frame_name),
            self._page_path(document)
        )

    def _get_titlepage(self, document: ZXDocument, page_title: str, add_frame: bool=True) -> ZXToken:
        page_title = page_title[0:(ZXScreen.SCREEN_WIDTH_CHARS-2)]
        zx_token = self.from_frame(
            self.resolve_frame_path('default_frame_title' if add_frame else 'default_title'),
            self._page_path(document)
        )
        zx_token.set_string(self.centered_position(page_title), 2, page_title)
        return zx_token

    def _page_path(self, document: ZXDocument, path_hint: str=None) -> Path:
        return self.generate_asset_path(document, document.get_next_asset_id(), ZXToken.FILE_EXTENSION, path_hint)

    @classmethod
    def centered_position(cls, text):
        return (ZXScreen.SCREEN_WIDTH_CHARS - len(text)) // 2
