from . import utilities

class ZXAttribute:
    # Attributes
    BLACK   = 0b00000000
    BLUE    = 0b00000001
    RED     = 0b00000010
    MAGENTA = 0b00000011
    GREEN   = 0b00000100
    CYAN    = 0b00000101
    YELLOW  = 0b00000110
    WHITE   = 0b00000111
    FLASH   = 0b10000000
    BRIGHT  = 0b01000000
    COLOURS = {
        'BLACK': BLACK,
        'BLUE': BLUE,
        'RED': RED, 
        'MAGENTA': MAGENTA, 
        'GREEN': GREEN, 
        'CYAN': CYAN, 
        'YELLOW': YELLOW, 
        'WHITE': WHITE
    }
    COLOUR_TOKENS = {v: k for k, v in COLOURS.items()}
    ATTRIBUTES = COLOURS | {
        'FLASH': FLASH,
        'BRIGHT': BRIGHT
    }
    ATTRIBUTE_TOKENS = {v: k for k, v in ATTRIBUTES.items()}

    ink: int
    paper: int
    is_bright: bool
    is_flashing: bool

    def __init__(self, is_flashing: bool=False, is_bright: bool=False, paper: int=BLACK, ink: int=WHITE):
        self.ink = ink
        self.paper = paper
        self.is_bright = bool(is_bright)
        self.is_flashing = bool(is_flashing)

    def __int__(self):
        return int(
            (self.FLASH if self.is_flashing else 0x00) | 
            (self.BRIGHT if self.is_bright else 0x00) | 
            (self.paper << 3) |
            self.ink
        )

    @property
    def ink(self):
        return self._ink

    @ink.setter
    def ink(self, colour: int):
        self._ink = colour % (self.WHITE + 1)

    @property
    def paper(self):
        return self._paper

    @paper.setter
    def paper(self, colour: int):
        self._paper = colour % (self.WHITE + 1)

    def swap(self) -> ZXAttribute:
        '''
        Swaps ink and paper
        '''
        self.ink, self.paper = self.paper, self.ink
        return self

    def set_ink(self, colour: int) -> ZXAttribute:
        self.ink = colour
        return self

    def set_paper(self, colour: int) -> ZXAttribute:
        self.paper = colour
        return self

    def set_bright(self, enabled: bool=False) -> ZXAttribute:
        self.is_bright = enabled
        return self

    def set_flash(self, enabled: bool=False) -> ZXAttribute:
        self.is_flashing = enabled
        return self

    def set_named(self, func_name, value):
        if func_name in (self.set_ink.__name__,
                         self.set_paper.__name__,
                         self.set_bright.__name__,
                         self.set_flash.__name__):
            return getattr(self, func_name)(value)
        raise ValueError(f'Invalid function name {func_name}')

    @classmethod
    def get_ink_from(cls, value: int) -> int:
        return int(value & 0b00000111) % (cls.WHITE + 1)

    @classmethod
    def get_paper_from(cls, value: int) -> int:
        return int((value & 0b00111000) >> 3) % (cls.WHITE + 1)

    @classmethod
    def get_is_flashing_from(cls, value: int) -> bool:
        return bool((value & cls.FLASH) == cls.FLASH)

    @classmethod
    def get_is_bright_from(cls, value: int) -> bool:
        return bool((value & cls.BRIGHT) == cls.BRIGHT)

    @classmethod
    def from_value(cls, value: int) -> ZXAttribute:
        return ZXAttribute(
            is_flashing=cls.get_is_flashing_from(value),
            is_bright=cls.get_is_bright_from(value),
            ink=cls.get_ink_from(value),
            paper=cls.get_paper_from(value)
        )

    @classmethod
    def tokenise(cls, attribute_value: int):
        '''
        Create string representation of each part of the attribute, mainly
        useful for logging purposes as anything graphical would be able to
        display this more nicely.
        '''
        attribute = cls.from_value(attribute_value)
        parts = []
        if attribute.is_flashing:
            parts.append(cls.tokenise_attribute(cls.FLASH))
        if attribute.is_bright:
            parts.append(cls.tokenise_attribute(cls.BRIGHT))
        parts.append(cls.tokenise_colour(attribute.ink))
        parts.append('on')
        parts.append(cls.tokenise_colour(attribute.paper))
        return parts

    @classmethod
    def tokenise_attribute(cls, value: int):
        '''
        Note that the function takes the numerical value of a token, not an
        attribute value.
        '''
        if not value in cls.ATTRIBUTE_TOKENS:
            raise ValueError(f'Invalid attribute {value=}')
        return cls.ATTRIBUTE_TOKENS[value]

    @classmethod
    def tokenise_colour(cls, colour: int):
        if not colour in cls.COLOUR_TOKENS:
            raise ValueError(f'Invalid value {colour=}')
        return cls.COLOUR_TOKENS[colour]