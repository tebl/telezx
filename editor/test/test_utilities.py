import unittest
from lib import utilities

class TestUtilities(unittest.TestCase):

    def test_format_padded_id(self):
        self.assertEqual(utilities.format_padded_id(1, width=1), '1')
        self.assertEqual(utilities.format_padded_id(1, width=2), '01')
        self.assertEqual(utilities.format_padded_id(1), '0001')

    def test_sanitize_filename(self):
        self.assertEqual(utilities.sanitize_filename('test'), 'test')
        print(utilities.sanitize_filename('test?#"!%&/&'))
        self.assertEqual(utilities.sanitize_filename('Test?#"!%&/&'), 'test')

    def test_suggest_document_name(self):
        self.assertEqual(utilities.suggest_document_name(1), '0001')
        self.assertEqual(utilities.suggest_document_name(1, 'Test'), '0001-Test')
