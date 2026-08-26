import unittest
from lib import utilities

class TestUtilities(unittest.TestCase):
    def test_format_padded_id(self):
        self.assertEqual(utilities.format_padded_id(1, width=1), '1')
        self.assertEqual(utilities.format_padded_id(1, width=2), '01')
        self.assertEqual(utilities.format_padded_id(1), '0001')

    def test_sanitize_filename(self):
        self.assertEqual(utilities.sanitize_filename('test'), 'test')
        self.assertEqual(utilities.sanitize_filename('Test?#"!%&/& '), 'Test')

    def test_suggest_document_directory(self):
        self.assertEqual(utilities.suggest_document_directory(1), '0001')
        self.assertEqual(utilities.suggest_document_directory(1, 'Test'), '0001-Test')
        self.assertEqual(utilities.suggest_document_directory(1, 'Test?#"!%&/& '), '0001-Test')

    def test_suggest_asset_path(self):
        self.assertEqual(utilities.suggest_asset_path(0, '.scr'), '00.scr')
        self.assertEqual(utilities.suggest_asset_path(0, '.scr', 'test'), '00-test.scr')
        self.assertEqual(utilities.suggest_asset_path(0, '.scr', 'test.scr'), '00-test.scr')
        self.assertEqual(utilities.suggest_asset_path(0, '.scr', 'Test?#"!%&/& '), '00-Test.scr')
