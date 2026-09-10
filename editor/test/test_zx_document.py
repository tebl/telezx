import unittest
from lib import utilities, ZXDocument, ReadableIdentifierIterator, ZXPage

class TestZXDocument(unittest.TestCase):
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