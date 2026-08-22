from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class AssetHelper(RepositoryHelper):
    def __init__(self, repository: Path):
        super().__init__(repository)


    def create_frames(self, indent: int=0):
        base_path = self.repository / 'src' / 'assets'
        self.logger.info(f'Creating frames in {base_path}', indent=indent)
        for colour, value, title_value in ZXFrame.frame_colours():
            frame_path = base_path / f'frame_{colour}{ZXToken.FILE_EXTENSION}'
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_box(value, title_value)
            frame.save()
            frame.set_string(1, 2, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.debug(f'{frame_path.name} created.', indent=indent+1)

            frame_path = base_path / f'frame_{colour}_title{ZXToken.FILE_EXTENSION}'
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title_box(value, title_value)
            frame.save()
            frame.set_string(1, 2, 'Title here')
            frame.set_string(1, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.debug(f'{frame_path.name} created.', indent=indent+1)

            frame_path = base_path / f'title_{colour}{ZXToken.FILE_EXTENSION}'
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title(value, title_value)
            frame.save()
            frame.set_string(2, 2, 'Title here')
            frame.set_string(0, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.debug(f'{frame_path.name} created.', indent=indent+1)
