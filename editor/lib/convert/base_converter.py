from .. import ZXToken, ZXDocument, ZXLogger

class BaseConverter:
    @classmethod
    def debug(cls, *segments, indent=0):
        ZXLogger.get_instance().debug(*segments, indent=indent)

    @classmethod
    def error(cls, *segments, indent=0):
        ZXLogger.get_instance().error(*segments, indent=indent)

    @classmethod
    def info(cls, *segments, indent=0):
        ZXLogger.get_instance().info(*segments, indent=indent)

    @classmethod
    def warning(cls, *segments, indent=0):
        ZXLogger.get_instance().warning(*segments, indent=indent)

    @classmethod
    def get_format_suffix(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def _log_export(cls, suffix: str, output_path: Path):
        cls.info('Exporting', suffix[1:], 'to', output_path.name)
