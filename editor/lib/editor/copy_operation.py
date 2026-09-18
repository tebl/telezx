from .screen_region import ScreenCoordinate
from .. import CellCopy, ZXFont

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

    @classmethod
    def get_single_character(cls, copy_operation: CopyOperation|None) -> str:
        for cell in copy_operation.cells:
            return cell.cell_copy.char_code
        return ZXFont.ASCII_SPACE

    @classmethod
    def is_single_character(cls, copy_operation: CopyOperation|None) -> bool:
        if not copy_operation:
            return False
        return copy_operation.shape == (1,1)

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
