from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class DocumentHelper(RepositoryHelper):
    def __init__(self, repository: Path):
        super().__init__(repository)

    def create_document(self, document_id, path_hint=None) -> ZXDocument:
        if self.open_document(document_id, allow_none=True) is not None:
            raise FileExistsError(f'Document ID {document_id} already exists')

        document_path = self.generate_document_path(document_id, path_hint)
        document_path.parent.mkdir()
        document = ZXDocument(document_path, document_id)
        document.save()
        return document
    
    def open_document(self, document_id, allow_none=False) -> ZXDocument:
        try:
            return ZXDocument.from_document_id(document_id, self.src_path)
        except FileNotFoundError:
            if not allow_none:
                raise
        return None

    def copy_token(self, document: ZXDocument, document_path: Path, export_format=None) -> bool:
        '''
        In effect this makes a copy of the specified ZXToken-file and adds a
        reference to it in the document.
        '''
        return self.create_token(document, document_path, export_format)
    
    def create_token(self, document: ZXDocument, frame_path=None, export_format=None) -> bool:
        asset_path = self.generate_token_path(document, document.get_next_page_id())
        zx_token = self.generate_zx_token(asset_path, frame_path)
        zx_token.save()

        if not export_format:
            export_format = 'TKN'
        ZXPage_Token(document, zxtoken_path=zx_token.document_path, export_format=export_format)

        return document.save()