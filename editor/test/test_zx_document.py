import unittest
from lib import utilities, ZXDocument, ReadableIdentifierIterator

class TestZXDocument(unittest.TestCase):
    def test_readable_id_iterator(self):
        iterator = ReadableIdentifierIterator(start=0x1000)
        for i in range(16):
            value = next(iterator)
            # Check that all parts returned are
            # always 0-9 (ignoring A-F).
            self.assertLess(value % 16, 11)