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
        h = ScreenRegion(ScreenCoordinate(1, 1), ScreenCoordinate(2, 2))
        self.assertEqual([coord.get() for coord in h.cells(CellDirection.WEST)], [(1, 1), (1, 2), (2, 1), (2,2)])
        self.assertEqual([coord.get() for coord in h.cells(CellDirection.EAST)], [(2, 1), (2, 2), (1, 1), (1, 2)])
        self.assertEqual([coord.get() for coord in h.cells(CellDirection.NORTH)], [(1, 1), (2, 1), (1, 2), (2, 2)])
        self.assertEqual([coord.get() for coord in h.cells(CellDirection.SOUTH)], [(1, 2), (2, 2), (1, 1), (2, 1)])

    def test_inside_region(self):
        h = ScreenRegion(ScreenCoordinate(10, 15), ScreenCoordinate(15, 20))
        self.assertTrue(h.is_inside(11, 15))
        self.assertTrue(h.is_inside(14, 19))
        self.assertTrue(h.is_inside(10, 15))
        self.assertTrue(h.is_inside(15, 20))

        self.assertFalse(h.is_inside(1, 2))
        self.assertFalse(h.is_inside(16, 20))

    def __get_coordinates(self, screen_region):
        return tuple([c.get() for c in screen_region.coordinates()])