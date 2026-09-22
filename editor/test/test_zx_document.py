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
        self.assertTrue(doc.save())

    def test_field_persistence(self):
        document_id = 0x1000
        document_path = self.get_document_path(document_id, 'Test page')
        doc = ZXDocument(self.repository_path, 
                         document_path, 
                         document_id,
                         description='test description',
                         abbreviation='Short',
                         link_a=0x2000, link_a_txt='LNK_A',
                         link_b=0x3000, link_b_txt='LNK_B',
                         link_c=0x4000, link_c_txt='LNK_C',
                         tags=['test_tag', 'test_tag2'],
                         include_toc=True)
        self.assertTrue(doc.save())

        res = ZXDocument.from_document_id(self.repository_path, document_id)
        self.assertEqual(res.document_id, document_id)
        self.assertEqual(res.description, 'test description')
        self.assertEqual(res.abbreviation, 'Short')
        self.assertEqual(res.link_a, 0x2000)
        self.assertEqual(res.link_b, 0x3000)
        self.assertEqual(res.link_c, 0x4000)
        self.assertEqual(res.link_a_txt, 'LNK_A')
        self.assertEqual(res.link_b_txt, 'LNK_B')
        self.assertEqual(res.link_c_txt, 'LNK_C')
        self.assertEqual(res.include_toc, True)
        self.assertEqual(res.tags, ['test_tag', 'test_tag2'])

    def test_export(self):
        self.registry.sync_record(0x1001, description="Page1", abbreviation='p1')

        document_id = 0xffff
        doc_path = self.get_document_path(document_id, path_hint='Test page')
        doc = ZXDocument(self.repository_path, 
                         doc_path, 
                         document_id, 
                         description='Test page', 
                         abbreviation='Test', 
                         link_a=0x1001,
                         link_b=0x1002, link_b_txt='Page2',
                         link_c=0x1003,
                         tags=['test_tag'])
        ZXPage_ClearText(doc)
        self.assertTrue(doc.save())

        # Reload document
        doc = ZXDocument.from_document_id(self.repository_path, document_id)

        doc.export(output_directory=self.repository_out_path, registry=self.registry, sync_registry=True)
        index_path = self.repository_out_path / 'FFFF' / 'FFFF.idx'
        self.assertTrue(index_path.is_file())
        with open(index_path, 'rb') as file:
            content = file.read()
            content = content.decode("utf-8").replace('\0', ' ')
            # Index structure:
            # ADDR Field              Bytes
            # 0x00 IDX                3
            # 0x03 Page count (hex)   2
            # 0x05 Link A             4
            # 0x09 Link A TXT (8+\0)  9
            # 0x12 Link B             4
            # 0x16 Link B TXT (8+\0)  9
            # 0x1f Link C             4
            # 0x23 Link C TXT (8+\0)  9
            # 0x2c <unused>           20
            # 0x40 Page 0 type (hex)  2
            # 0x42 Page 0 parameter   2
            self.assertEqual(content[0:3], 'IDX')
            self.assertEqual(content[3:5], '01')                # Page count
            self.assertEqual(content[5:9], '1001')
            self.assertEqual(content[9:18].strip(), 'p1')       # From registry
            self.assertEqual(content[18:22], '1002')
            self.assertEqual(content[22:31].strip(), 'Page2')   # Specified directly
            self.assertEqual(content[31:35], '1003')
            self.assertEqual(content[35:44].strip(), '0x1003')  # Missing both, generated
            # print(content)

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