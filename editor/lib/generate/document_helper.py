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
        document = ZXDocument(self.repository, document_path, document_id)
        document.save()
        return document
    
    def open_document(self, document_id, allow_none=False) -> ZXDocument:
        try:
            return ZXDocument.from_document_id(self.repository, document_id)
        except FileNotFoundError:
            if not allow_none:
                raise
        return None

    def export_document(self, document: ZXDocument, registry: ZXRegistry) -> bool:
        return document.export(self.out_path, registry)

    def copy_token(self, document: ZXDocument, document_path: Path, export_format=None) -> bool:
        '''
        In effect this makes a copy of the specified ZXToken-file and adds a
        reference to it in the document.
        '''
        return self.create_token(document, document_path, export_format)
    
    def create_token(self, document: ZXDocument, frame_path: Path=None, export_format=None) -> bool:
        asset_path = self.generate_token_path(document, document.get_next_page_id())
        zx_token = self.generate_zx_token(asset_path, frame_path)
        zx_token.save()

        if not export_format:
            export_format = 'TKN'
        ZXPage_Token(document, zxtoken_path=zx_token.document_path, export_format=export_format)
        return document.save()

    def link_token(self, document: ZXDocument, document_path: Path, export_format=None) -> bool:
        document_path = self.get_path_relative_to(document, document_path)
        if not export_format:
            export_format = 'TKN'
        ZXPage_Token(document, zxtoken_path=document_path, export_format=export_format)
        return document.save()

    def create_text(self, document: ZXDocument, frame_path: Path=None, text_lines: list[str]=None, text_attribute=ZXToken.UNSPECIFIED) -> bool:
        if not text_lines:
            text_lines = ZXPage_ClearText.blank_text()
        if frame_path:
            frame_path = self.get_path_relative_to(document, frame_path)
        ZXPage_ClearText(document, frame_path, text_lines, text_attribute)
        return document.save()