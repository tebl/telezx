from .screen_region import ScreenCoordinate
from .. import CellCopy

class CopyOperation:
    shape: tuple[int, int]
    cells: list[CopyData]

    def __init__(self, shape: tuple[int, int], cells: list[CopyData]):
        self.shape = shape
        self.cells = cells

    def __str__(self):
        x, y = self.shape
        return f'{x}x{y} cells'

    def count(self) -> int:
        x, y = self.shape
        return x*y


class CopyData:
    coordinate: ScreenCoordinate
    cell_copy: CellCopy

    def __init__(self, coordinate: ScreenCoordinate, cell_copy: CellCopy):
        self.coordinate = coordinate
        self.cell_copy = cell_copy

    def get_relative_to(self, cursor: ScreenCoordinate) -> tuple[int, int]:
        return (
            cursor.char_x + self.coordinate.char_x,
            cursor.char_y + self.coordinate.char_y
        )
