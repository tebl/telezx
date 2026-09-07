import unittest
from lib import CellDirection, ScreenRegion, ScreenCoordinate, ScreenNavigator

class TestEditor(unittest.TestCase):
    def test_navigation_next(self):
        region = ScreenRegion.from_tuples((10, 10), (15, 15))

        cursor = ScreenCoordinate(10, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.next(cursor, region), cursor), (True, (11, 10)))
        cursor = ScreenCoordinate(15, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.next(cursor, region), cursor), (True, (10, 11)))
        cursor = ScreenCoordinate(15, 15)
        self.assertEqual(self.__get_results(ScreenNavigator.next(cursor, region), cursor), (False, (15, 15)))

        # Cursor position should be updated with something valid for the region
        cursor = ScreenCoordinate(31, 15)
        self.assertEqual(self.__get_results(ScreenNavigator.next(cursor, region), cursor), (True, (15, 15)))


    def test_navigation_previous(self):
        region = ScreenRegion.from_tuples((10, 10), (15, 15))

        cursor = ScreenCoordinate(11, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.previous(cursor, region), cursor), (True, (10, 10)))

        cursor = ScreenCoordinate(10, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.previous(cursor, region), cursor), (False, (10, 10)))
        cursor = ScreenCoordinate(10, 15)
        self.assertEqual(self.__get_results(ScreenNavigator.previous(cursor, region), cursor), (True, (15, 14)))

        # Cursor position should be updated with something valid for the region
        cursor = ScreenCoordinate(31, 15)
        self.assertEqual(self.__get_results(ScreenNavigator.previous(cursor, region), cursor), (True, (15, 15)))


    def test_navigation_newline(self):
        region = ScreenRegion.full()
        cursor = ScreenCoordinate(10, 0)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (True, (0, 1)))
        cursor = ScreenCoordinate(0, 23)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (False, (0, 23)))
        cursor = ScreenCoordinate(20, 23)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (False, (20, 23)))
        cursor = ScreenCoordinate(31, 23)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (False, (31, 23)))

        region = ScreenRegion.from_tuples((10, 10), (15, 15))
        cursor = ScreenCoordinate(11, 11)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (True, (10, 12)))
        cursor = ScreenCoordinate(14, 15)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (False, (14, 15)))
        # Cursor position should be updated with something valid for the region
        cursor = ScreenCoordinate(30, 13)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (True, (15, 13)))

        region = ScreenRegion.from_tuples((10, 10), (30, 10))
        cursor = ScreenCoordinate(14, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (False, (14, 10)))
        # Cursor position should be updated with something valid for the region
        cursor = ScreenCoordinate(31, 10)
        self.assertEqual(self.__get_results(ScreenNavigator.newline(cursor, region), cursor), (True, (30, 10)))



    def __get_results(self, updated, cursor: ScreenCoordinate):
        return (updated, cursor.get())

    def __get_coordinates(self, screen_region):
        return tuple([c.get() for c in screen_region.coordinates()])