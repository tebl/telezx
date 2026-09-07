import enum
from .. import ZXScreen, utilities


class CellDirection(enum.Enum):
    ANY = enum.auto()
    NORTH = enum.auto()
    SOUTH = enum.auto()
    EAST = enum.auto()
    WEST = enum.auto()

    def get_delta(self):
        match self:
            case self.NORTH:
                return (0, -1)
            case self.SOUTH:
                return (0, 1)
            case self.EAST:
                return (1, 0)
            case self.WEST:
                return (-1, 0)
            case _:
                raise ValueError(f'Unknown direction {self}')


class ScreenCoordinate:
    char_x: int
    char_y: int

    def __init__(self, char_x: int, char_y: int):
        self.set(char_x, char_y)

    def get(self):
        return (self.char_x, self.char_y)

    def set(self, char_x, char_y):
        self.char_x = (char_x % ZXScreen.SCREEN_WIDTH_CHARS)
        self.char_y = (char_y % ZXScreen.SCREEN_HEIGHT_CHARS)

    def move(self, direction: CellDirection):
        match direction:
            case CellDirection.NORTH:
                if self.can_move_north():
                    self.move_north()
            case CellDirection.SOUTH:
                if self.can_move_south():
                    self.move_south()
            case CellDirection.EAST:
                if self.can_move_east():
                    self.move_east()
            case CellDirection.WEST:
                if self.can_move_west():
                    self.move_west()
            case _:
                raise ValueError(f'Unknown direction {direction}')

    def move_east(self):
        self.char_x = (self.char_x + 1) % ZXScreen.SCREEN_WIDTH_CHARS

    def move_north(self):
        self.char_y = (self.char_y - 1) % ZXScreen.SCREEN_HEIGHT_CHARS

    def move_south(self):
        self.char_y = (self.char_y + 1) % ZXScreen.SCREEN_HEIGHT_CHARS

    def move_west(self):
        self.char_x = (self.char_x - 1) % ZXScreen.SCREEN_WIDTH_CHARS

    def can_move(self, direction: CellDirection):
        match direction:
            case CellDirection.NORTH:
                return self.can_move_north()
            case CellDirection.SOUTH:
                return self.can_move_south()
            case CellDirection.EAST:
                return self.can_move_east()
            case CellDirection.WEST:
                return self.can_move_west()
        raise ValueError(f'Unknown direction {direction}')

    def can_move_east(self):
        return self.char_x <= (ZXScreen.SCREEN_WIDTH_CHARS - 2)

    def can_move_north(self):
        return self.char_y > 0

    def can_move_south(self):
        return self.char_y <= (ZXScreen.SCREEN_HEIGHT_CHARS - 2)

    def can_move_west(self):
        return self.char_x > 0

    def __eq__(self, value):
        return (self.char_x == value.x and self.char_y == value.y)


class ScreenRegion:
    coord_start: ScreenCoordinate
    coord_end: ScreenCoordinate

    def __init__(self, coord_a: ScreenCoordinate, coord_b: ScreenCoordinate):
        self.coord_start = self.get_filtered_coordinate(min, coord_a, coord_b)
        self.coord_end = self.get_filtered_coordinate(max, coord_a, coord_b)

    def can_transpose(self, direction):
        '''
        Determine if we can transpose the selection in the specified direction.
        '''
        match direction:
            case CellDirection.NORTH:
                return self.can_transpose_north()
            case CellDirection.SOUTH:
                return self.can_transpose_south()
            case CellDirection.EAST:
                return self.can_transpose_east()
            case CellDirection.WEST:
                return self.can_transpose_west()
        raise ValueError(f'Unknown direction {direction}')

    def can_transpose_east(self):
        return self.coord_end.can_move_east()

    def can_transpose_north(self):
        return self.coord_start.can_move_north()

    def can_transpose_south(self):
        return self.coord_end.can_move_south()

    def can_transpose_west(self):
        return self.coord_start.can_move_west()

    def cells(self, from_direction: CellDirection):
        match from_direction:
            case CellDirection.NORTH | CellDirection.ANY:
                for char_y in range(self.coord_start.char_y, self.coord_end.char_y + 1):
                    for char_x in range(self.coord_start.char_x, self.coord_end.char_x + 1):
                        yield ScreenCoordinate(char_x, char_y)
            case CellDirection.SOUTH:
                for char_y in range(self.coord_end.char_y, self.coord_start.char_y - 1, -1):
                    for char_x in range(self.coord_start.char_x, self.coord_end.char_x + 1):
                        yield ScreenCoordinate(char_x, char_y)
            case CellDirection.EAST:
                for char_x in range(self.coord_end.char_x, self.coord_start.char_x - 1, -1):
                    for char_y in range(self.coord_start.char_y, self.coord_end.char_y + 1):
                        yield ScreenCoordinate(char_x, char_y)
            case CellDirection.WEST:
                for char_x in range(self.coord_start.char_x, self.coord_end.char_x + 1):
                    for char_y in range(self.coord_start.char_y, self.coord_end.char_y + 1):
                        yield ScreenCoordinate(char_x, char_y)
            case _:
                raise ValueError('Unknown direction')

    def coordinates(self):
        return (self.coord_start, self.coord_end)

    def is_inside(self, char_x, char_y):
        if not (char_x >= self.coord_start.char_x and char_x <= self.coord_end.char_x):
            return False
        if not (char_y >= self.coord_start.char_y and char_y <= self.coord_end.char_y):
            return False
        return True

    def transpose(self, direction: CellDirection):
        self.coord_start.move(direction)
        self.coord_end.move(direction)

    def transpose_west(self):
        self.coord_start.move(CellDirection.WEST)
        self.coord_end.move(CellDirection.WEST)

    def transpose_east(self):
        self.coord_start.move(CellDirection.EAST)
        self.coord_end.move(CellDirection.EAST)

    def transpose_north(self):
        self.coord_start.move(CellDirection.NORTH)
        self.coord_end.move(CellDirection.NORTH)

    def transpose_south(self):
        self.coord_start.move(CellDirection.SOUTH)
        self.coord_end.move(CellDirection.SOUTH)

    @classmethod
    def get_filtered_coordinate(cls, func, coord_a: ScreenCoordinate, coord_b: ScreenCoordinate):
        return ScreenCoordinate(
            char_x = func(coord_a.char_x, coord_b.char_x), 
            char_y = func(coord_a.char_y, coord_b.char_y)
        )

    @classmethod
    def from_tuples(cls, coord_a: tuple[int, int], coord_b: tuple[int, int]):
        return ScreenRegion(
            ScreenCoordinate(char_x = coord_a[0], char_y = coord_a[1]),
            ScreenCoordinate(char_x = coord_b[0], char_y = coord_b[1])
        )