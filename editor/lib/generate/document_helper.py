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