class ZXLogger:
    LOG_ERR = 3
    LOG_WARNING = 4
    LOG_INFO = 6
    LOG_DEBUG = 7
    _instance = None

    def __init__(self):
        raise RuntimeError("Incorrect usage, see get_instance()")

    def log(self, message, priority):
        if self.check_priority(priority):
            print(self.format_message(message, priority))

    def error(self, *segments):
        self.log(self.__join_segments(segments), self.LOG_ERR)

    def warning(self, *segments):
        self.log(self.__join_segments(segments), self.LOG_WARNING)

    def info(self, *segments):
        self.log(self.__join_segments(segments), self.LOG_INFO)

    def debug(self, *segments):
        self.log(self.__join_segments(segments), self.LOG_DEBUG)

    def __join_segments(self, segments):
        return ' '.join(map(str, segments))

    def check_priority(self, priority) -> bool:
        return (priority <= self.log_level)

    def format_message(self, message, priority) -> str:
        return "[{}] {}".format(self.to_priority_string(priority), message)

    def set_log_level(self, log_level):
        self.log_level = log_level
        return self

    @classmethod
    def to_priority_string(cls, priority):
        match priority:
            case cls.LOG_ERR:
                return 'E'
            case cls.LOG_WARNING:
                return 'W'
            case cls.LOG_INFO:
                return 'I'
            case cls.LOG_DEBUG:
                return 'D'
            case _:
                return 'U'

    @classmethod
    def get_instance(cls) -> ZXLogger:
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.set_log_level(cls.LOG_INFO)
        return cls._instance