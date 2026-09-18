from .. import ZXScreen, CellCopy

class UndoOperation:
    entries: dict[(int, int), CellCopy]

    def __init__(self):
        self.entries = {}

    def add_cell(self, char_x, char_y, cell_copy: CellCopy) -> UndoOperation:
        '''
        Add entries, but note we'll actively discard any information about any
        subsequent updates to a specific coordinate. Doing it this way ensures
        that we can roll back everything consistently.
        '''
        if not (char_x, char_y) in self.entries:
            self.entries[(char_x, char_y)] = cell_copy
        return self

    def items(self):
        return self.entries.items()

    def size(self):
        return len(self.entries)
