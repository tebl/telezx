import unittest, tempfile
from pathlib import Path
from lib import utilities, ZXDocument, ReadableIdentifierIterator, ZXPage, ZXPage_ClearText, ZXRegistry

class TestZXDocument(unittest.TestCase):
    def setUp(self):
        self.repository = tempfile.TemporaryDirectory(prefix='telezx-repository-')
        self.repository_path = Path(self.repository.name)
        self.repository_out_path = self.repository_path / ZXDocument.PATH_OUT
        self.registry_path = Path(self.repository.name) / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
        self.registry = ZXRegistry.create_file(document_path=self.registry_path, allow_overwrite=False)

    def tearDown(self):
        self.repository.cleanup()

    def debug_contents(self, document_path):
        with open(document_path, 'r') as file:
            print(file.read())

    def get_document_path(self, document_id, path_hint):
        return self.repository_path / 'src' / utilities.suggest_document_directory(document_id, path_hint) / f'document{ZXDocument.EXTENSION_DOCUMENT}'

    def test_create(self):
        document_id = 0x1000
        doc_path = self.get_document_path(document_id, 'Test page')
        doc = ZXDocument(self.repository_path, doc_path, document_id)
        doc.save()

    def test_create_contents(self):
        document_id = 0x1000
        doc_path = self.get_document_path(document_id, path_hint='Test page')
        doc = ZXDocument(self.repository_path, 
                         doc_path, 
                         document_id, 
                         description='Test page', 
                         abbreviation='Test', 
                         link_a=0x1001, link_a_txt='Page1',
                         link_b=0x1002, link_b_txt='Page2',
                         link_c=0x1003, link_c_txt='Page3',
                         tags=['test_tag'])
        doc.save()

        doc = ZXDocument.from_document_id(self.repository_path, document_id)
        self.assertEqual(doc.document_id, document_id)
        self.assertEqual(doc.description, 'Test page')
        self.assertEqual(doc.abbreviation, 'Test')
        self.assertEqual(doc.tags, ['test_tag'])

    def test_export(self):
        document_id = 0xffff
        doc_path = self.get_document_path(document_id, path_hint='Test page')
        doc = ZXDocument(self.repository_path, 
                         doc_path, 
                         document_id, 
                         description='Test page', 
                         abbreviation='Test', 
                         link_a=0x1001, link_a_txt='Page1',
                         link_b=0x1002, link_b_txt='Page2',
                         link_c=0x1003, link_c_txt='Page3',
                         tags=['test_tag'])
        ZXPage_ClearText(doc)

        doc.export(output_directory=self.repository_out_path, registry=self.registry, sync_registry=True)
        index_path = self.repository_out_path / 'FFFF' / 'FFFF.idx'
        self.assertTrue(index_path.is_file())
        text_path = self.repository_out_path / 'FFFF' / 'FFFF.00.tkn'
        self.assertTrue(text_path.is_file())

        # Check that the entries appeared up in registry
        self.assertIsNotNone(self.registry.lookup(document_id))

    def test_readable_id_iterator(self):
        iterator = ReadableIdentifierIterator(start=0x1000)
        for i in range(16):
            value = next(iterator)
            # Check that all parts returned are
            # always 0-9 (ignoring A-F).
            self.assertLess(value % 16, 11)

    def test_find_text_links(self):
        self.assertEqual([m for m in ZXPage.find_text_links('  abcd [AABB] efghi  ')], [(7, 13, ' AABB ')])
        self.assertEqual([m for m in ZXPage.find_text_links('[AABB] efghi [55aa]')], [(0, 6, ' AABB '), (13, 19, ' 55AA ')])

        # Should not match any of these
        self.assertEqual([m for m in ZXPage.find_text_links('  abcd [AABBCC] efghi  ')], [])
        self.assertEqual([m for m in ZXPage.find_text_links('  abcd [AA] efghi  ')], [])
        self.assertEqual([m for m in ZXPage.find_text_links('  abcd [AAFx] efghi  ')], [])