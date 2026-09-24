import unittest, tempfile, string
from pathlib import Path
from lib import utilities, ZXFont, ZXGlyph

class TestZXGlyph(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix='telezx-registry-')

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_font(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_default.bin'
        font = ZXFont.from_file(path=font_path, generate_rgb=True)
        self.assertIsNotNone(font)
        self.assertGreater(font.get_glyph_count(), 0)

        for char_code, data in font.glyphs():
            self.assertEqual(len(data), 8)
            self.assertGreaterEqual(char_code, ZXFont.ASCII_SPACE)
            self.assertLessEqual(char_code, ZXFont.ASCII_COPYRIGHT)

    def test_write_font(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_default.bin'
        font = ZXFont.from_file(path=font_path, generate_rgb=True)
        self.assertIsNotNone(font)
        self.assertGreater(font.get_glyph_count(), 0)

        # Read binary file for comparison
        font_bin = self.__get_contents(font_path, 'rb')
        self.assertIsNotNone(font_bin)

        # Write font
        font_out = Path(self.temp_dir.name) / 'font_test.bin'
        self.assertFalse(font_out.is_file())
        font.write(font_out)
        self.assertTrue(font_out.is_file())

        # Read and compare to original
        self.assertEqual(font_bin, self.__get_contents(font_out, 'rb'))

    def test_write_glyph(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_glyphs.bin'
        font = ZXGlyph.from_file(path=font_path, generate_rgb=True)
        self.assertIsNotNone(font)
        self.assertGreater(font.get_glyph_count(), 0)

        # Read binary file for comparison
        font_bin = self.__get_contents(font_path, 'rb')
        self.assertIsNotNone(font_bin)

        # Write font
        font_out = Path(self.temp_dir.name) / 'font_test.bin'
        self.assertFalse(font_out.is_file())
        font.write(font_out)
        self.assertTrue(font_out.is_file())

        # Read and compare to original
        self.assertEqual(font_bin, self.__get_contents(font_out, 'rb'))

    def __get_contents(self, path: Path, mode: str) -> bytes:
        with open(path, mode) as file:
            return file.read()

    def test_add_glyph(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_glyphs.bin'
        font = ZXGlyph.from_file(path=font_path, generate_rgb=True)
        self.assertIsNotNone(font)
        font_count = font.get_glyph_count()
        self.assertGreater(font_count, 0)

        font.add_glyph([0, 1, 2, 3, 4, 5, 6, 7])
        font_out = Path(self.temp_dir.name) / 'font_test.bin'
        font.write(font_out)

        font = ZXGlyph.from_file(path=font_out, generate_rgb=True)
        self.assertEqual([v for v in font.get_offset(font.get_glyph_count() - 1)],
                         [0, 1, 2, 3, 4, 5, 6, 7])        

    def test_load_glyph(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_glyphs.bin'
        glyphs = ZXGlyph.from_file(path=font_path, generate_rgb=True)
        self.assertIsNotNone(glyphs)
        self.assertGreater(glyphs.get_glyph_count(), 0)

    def test_export_js(self):
        font_path = utilities.get_project_root() / 'fonts' / 'font_default.bin'
        font = ZXFont.from_file(path=font_path, generate_rgb=False)
        self.assertIsNotNone(font)
        self.assertGreater(font.get_glyph_count(), 0)

        export_path = Path(self.temp_dir.name) / 'export.js'
        font.export_js(export_path, 'DEFAULT')
        self.assertTrue(export_path.is_file())
        # print(self.__get_contents(export_path, 'r'))
