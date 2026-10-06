import unittest
from lib import ZXAttribute

class TestZXAttribute(unittest.TestCase):
    def test_attribute(self):
        a = ZXAttribute.from_value(0x32)
        self.assertEqual(a.ink, ZXAttribute.RED)
        self.assertEqual(a.paper, ZXAttribute.YELLOW)
        self.assertFalse(a.is_flashing)
        self.assertFalse(a.is_bright)

        a = ZXAttribute.from_value(0xf2)
        self.assertEqual(a.ink, ZXAttribute.RED)
        self.assertEqual(a.paper, ZXAttribute.YELLOW)
        self.assertTrue(a.is_flashing)
        self.assertTrue(a.is_bright)

    def test_overflow(self):
        a = ZXAttribute(is_bright=True, ink=44, paper=ZXAttribute.BLACK)
        self.assertTrue(a.is_bright)
        self.assertGreaterEqual(a.ink, ZXAttribute.BLACK)
        self.assertLessEqual(a.ink, ZXAttribute.WHITE)

        a = ZXAttribute.from_value(0)
        self.assertEqual(a.ink, ZXAttribute.BLACK)
        a.ink = 55
        self.assertGreaterEqual(a.ink, ZXAttribute.BLACK)
        self.assertLessEqual(a.ink, ZXAttribute.WHITE)