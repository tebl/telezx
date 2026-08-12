from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage_Overlay, ZXPage_TeleZX, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities
ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

class TOCGenerator:
    registry_path: Path
    pages_path: Path
    output_path: Path

    def __init__(self, registry_path: Path, pages_path: Path, output_path: Path):
        self.registry = ZXRegistry.from_file(registry_path, allow_create=True)
        self.pages_path = pages_path
        self.output_path = output_path

    def create_toc(self, document_id_start = 9900):
        document_id = document_id_start
        page_id = 0
        current_y = 4
        current_letter = None

        current_page = self.__get_titlepage(document_id, page_id, 'A-Z')
        for letter, items in self.registry.generate_TOC_AZ():
            # next letter in the alphabet
            if not letter == current_letter:
                current_letter = letter
                current_page.set_string(1, current_y, f' {current_letter} ', ZXScreen.to_attribute(is_bright=True, paper=ZXScreen.BLUE, ink=ZXScreen.WHITE))

            # enumerate items
            for description, link_id in items:
                current_page.set_string(5, current_y, description[0:21])
                current_page.set_string(27, current_y, link_id)

                # traverse pages, adding as needed
                if current_y >= 20:
                    current_y = 3
                    if page_id >= 99:
                        current_page.save()
                        document_id += 1
                        page_id = 0
                        current_page = self.__get_page(document_id, page_id)
                    else:
                        current_page.save()
                        page_id += 1
                        current_page = self.__get_page(document_id, page_id)
                else:
                    current_y += 1

        current_page.save()

    def __get_page(self, document_id, page_id) -> ZXToken:
        return self.__load_frame(
            'frame_blue',
            self.__page_path(document_id, page_id)
        )

    def __get_titlepage(self, document_id, page_id, title) -> ZXToken:
        zx_token = self.__load_frame(
            'frame_blue_title',
            self.__page_path(document_id, page_id)
        )
        zx_token.set_string(2, 2, title)
        return zx_token

    def __page_path(self, document_id, page_id):
        directory = self.pages_path / utilities.page_filename(document_id, 'TOC')
        directory.mkdir(exist_ok=True)
        return directory / "{}.{}{}".format(
            utilities.format_padded_id(document_id),
            utilities.format_padded_id(page_id, width=2),
            ZXToken.FILE_EXTENSION
        )

    def __load_frame(self, frame_name, page_path: Path):
        zx_token = ZXToken.from_file(Path(self.pages_path) / 'assets' / f'{frame_name}{ZXToken.FILE_EXTENSION}')
        zx_token.set_document(page_path)
        return zx_token

TOCGenerator(
    registry_path='pages/telezx.registry', 
    pages_path=Path('.') / 'pages',
    output_path=Path('.') / 'output'
).create_toc()