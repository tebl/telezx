from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXDocument, ZXFrame, ZXToken, utilities

class AssetHelper(RepositoryHelper):
    DEFAULT_DESCRIPTION = 'default'

    def __init__(self, repository: Path):
        super().__init__(repository)

    def create_frames(self, indent: int=0):
        frame_path = self.asset_path / self.get_filename()
        frame = ZXFrame.create_frame(frame_path)
        frame.overlay_skirt(ZXToken.DEFAULT_PAPER)
        frame.save()
        frame.set_string(1, 2, 'Example text')
        frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
        self.logger.info(f'{frame_path.name} created.', indent=indent)

        for description, using_ink, using_paper, text_attribute in ZXFrame.frame_colours():
            frame_path = self.asset_path / self.get_filename(description, has_frame=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_box(using_ink, using_paper, text_attribute)
            frame.save()
            frame.set_string(1, 2, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

            frame_path = self.asset_path / self.get_filename(description, has_frame=True, has_title=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title_box(using_ink, using_paper, text_attribute)
            frame.save()
            frame.set_string(1, 2, 'Title here')
            frame.set_string(1, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

            frame_path = self.asset_path / self.get_filename(description, has_title=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title(using_ink, using_paper, text_attribute)
            frame.overlay_skirt(using_paper)
            frame.save()
            frame.set_string(2, 2, 'Title here')
            frame.set_string(0, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

    def copy_default_frame(self, colour_name: str, global_asset: bool):
        base_path = utilities.get_project_root() / 'assets' if global_asset else self.asset_path
        self.__copy_default(base_path)
        self.__copy_default(base_path, colour_name, has_frame=True)
        self.__copy_default(base_path, colour_name, has_frame=True, has_title=True)
        self.__copy_default(base_path, colour_name, has_title=True)

    def __copy_default(self, base_path: Path, has_description: str|None=None, has_frame: bool=False, has_title: bool=False):
        path_src = self.asset_path / self.get_filename(has_description, has_frame, has_title)
        path_out = base_path / self.get_filename(self.DEFAULT_DESCRIPTION, has_frame, has_title)
        self.__copy_file(path_src, path_out)

        path_src = path_src.with_suffix(path_src.suffix + ZXDocument.EXTENSION_SCREENSHOT)
        path_out = path_out.with_suffix(path_out.suffix + ZXDocument.EXTENSION_SCREENSHOT)
        if path_src.is_file():
            self.__copy_file(path_src, path_out)
        elif path_out.is_file():
            self.logger.warning('Removing', path_out)
            path_out.unlink()

    def __copy_file(self, path_src, path_out):
        root = utilities.get_project_root()
        self.logger.info('Copy', path_src.relative_to(root), 
                          '->', path_out.relative_to(root))
        path_src.copy(path_out)

    def get_filename(self, has_description: str|None=None, has_frame: bool=False, has_title: bool=False):
        parts = []
        if has_description:
            parts.append(utilities.sanitize_filename(has_description))
        if has_frame:
            parts.append('frame')
        if has_title:
            parts.append('title')
        if not len(parts):
            parts.append('page')
        return '_'.join(parts) + ZXToken.FILE_EXTENSION