import unittest
from lib import CellDirection, ScreenRegion, ScreenCoordinate

class TestEditor(unittest.TestCase):
    def test_screen_region(self):
        # Test regular order, then reversed
        self.assertEqual(self.__get_coordinates(ScreenRegion(ScreenCoordinate(0, 4), ScreenCoordinate(3, 8))), ((0, 4), (3, 8)))
        self.assertEqual(self.__get_coordinates(ScreenRegion(ScreenCoordinate(3, 8), ScreenCoordinate(0, 4))), ((0, 4), (3, 8)))

        # single line
        self.assertEqual(self.__get_coordinates(ScreenRegion(ScreenCoordinate(3, 8), ScreenCoordinate(6, 8))), ((3, 8), (6, 8)))
        self.assertEqual(self.__get_coordinates(ScreenRegion(ScreenCoordinate(6, 8), ScreenCoordinate(3, 8))), ((3, 8), (6, 8)))

    def test_enumerate_cells(self):
        region = ScreenRegion(ScreenCoordinate(1, 1), ScreenCoordinate(2, 2))
        self.assertEqual([coord.get() for coord in region.cells(CellDirection.WEST)], [(1, 1), (1, 2), (2, 1), (2,2)])
        self.assertEqual([coord.get() for coord in region.cells(CellDirection.EAST)], [(2, 1), (2, 2), (1, 1), (1, 2)])
        self.assertEqual([coord.get() for coord in region.cells(CellDirection.NORTH)], [(1, 1), (2, 1), (1, 2), (2, 2)])
        self.assertEqual([coord.get() for coord in region.cells(CellDirection.SOUTH)], [(1, 2), (2, 2), (1, 1), (2, 1)])

    def test_inside_region(self):
        region = ScreenRegion(ScreenCoordinate(10, 15), ScreenCoordinate(15, 20))
        self.assertTrue(region.is_inside(11, 15))
        self.assertTrue(region.is_inside(14, 19))
        self.assertTrue(region.is_inside(10, 15))
        self.assertTrue(region.is_inside(15, 20))

        self.assertFalse(region.is_inside(1, 2))
        self.assertFalse(region.is_inside(16, 20))

    def test_region_limits(self):
        region = ScreenRegion.full()
        self.assertTrue(region.is_inside(0, 0))
        self.assertTrue(region.is_inside(31, 23))

        region = ScreenRegion.from_tuples((10, 10), (15, 15))
        cursor = ScreenCoordinate(region.min_char_x(), region.min_char_y())
        self.assertTrue(region.is_cursor_inside(cursor))
        cursor = ScreenCoordinate(region.max_char_x(), region.max_char_y())
        self.assertTrue(region.is_cursor_inside(cursor))


    def __get_coordinates(self, screen_region):
        return tuple([c.get() for c in screen_region.coordinates()])