from .. import KeyboardDialog

class EditorKeyboardDialog(KeyboardDialog):
    def __init__(self, master):
        super().__init__(master)

    def create_body(self, master):
        main = super().create_body(master)

        main.columnconfigure(0, weight=10, uniform='tag')
        # main.columnconfigure(1, weight=1, uniform='tag')
        # main.columnconfigure(2, weight=10, uniform='tag')

        self._create_section(
            'Shortcuts', 
            main, 0, 0,
            [
                ('Ctrl', None, 'N', 'New document'),
                ('Ctrl', None, 'O', 'Open document'),
                ('Ctrl', None, 'S', 'Save document'),
                ('Ctrl', None, 'G', 'Toggle grid display'),
                ('Ctrl', None, 'Q', 'Quit')
            ])

        # self._create_section(
        #     'Copy / Paste', 
        #     main, 0, 2,
        #     [
        #         ('Ctrl', None, 'C', 'Copy selected cells'),
        #         ('Ctrl', None, 'X', 'Cut selected cells'),
        #         ('Ctrl', None, 'V', 'Paste cell'),
        #         ('Ctrl', None, 'Z', 'Undo changes'),
        #     ])

        # self._create_section(
        #     'Editing', 
        #     main, 1, 0,
        #     [
        #         ('Insert', None, None, 'Toggle insertion mode'),
        #         (None, None, None, '(changes typing behavior in selection)'),
        #         ('Ctrl', None, 'F', 'Follow attribute memory'),
        #         ('Ctrl', None, 'I', 'Invert cell'),
        #         ('Ctrl', 'Shift', 'F', 'Swap ink/paper'),
        #         ('Ctrl', 'Shift', 'C', 'Copy cell attribute'),
        #         ('Ctrl', 'Shift', 'V', 'Paste cell attribute')
        #     ])

        # self._create_section(
        #     'Selection manipulation', 
        #     main, 1, 2,
        #     [
        #         (None, 'Shift', 'LMB', 'Set selection'),
        #         ('Ctrl', None, 'UP', 'Move selected cells up'),
        #         ('Ctrl', None, 'DOWN', 'Move selected cells down'),
        #         ('Ctrl', None, 'LEFT', 'Move selected cells left'),
        #         ('Ctrl', None, 'RIGHT', 'Move selected cells right'),
        #         (None, None, None, '(moving ereases content behind it)'),
        #         (None, 'Shift', 'UP', 'Shift selected cells up'),
        #         (None, 'Shift', 'DOWN', 'Shift selected cells down'),
        #         (None, 'Shift', 'LEFT', 'Shift selected cells left'),
        #         (None, 'Shift', 'RIGHT', 'Shift selected cells right'),
        #         (None, None, None, '(shifting moves content)')
        #     ])
