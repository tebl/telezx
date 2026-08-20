#!/usr/bin/python3
from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities, VERSION

class TOCGenerator:
    registry_path: Path
    documents_path: Path
    output_path: Path

    TOC_TITLE = 'Table of contents'
    TOC_ABBREVIATION = 'TOC'

    enable_preview = True

    def __init__(self, repository: Path):
        self.logger = ZXLogger.get_instance()
        self.repository = Path(repository)
        self.documents_path = self.repository / 'src'
        self.documents_path.mkdir(exist_ok=True)
        self.output_path = self.repository / 'out'
        self.output_path.mkdir(exist_ok=True)

        self.registry_path = self.repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
        self.registry = ZXRegistry.from_file(self.registry_path, allow_create=True)

    def create_toc(self, document_id_start = 9900):
        document_id = document_id_start
        self.__create_toc_index(document_id)

        registry_toc = self.registry.generate_TOC_AZ()
        for letter in self.registry.LETTERS_AZ:
            document_id += 1
            target_directory = self.__create_path(document_id, f'TOC-{letter}')

            with self.__get_document(document_id, f'{self.TOC_TITLE} ({letter})', f'TOC-{letter}', target_directory) as document:
                document.link_a = document_id_start
                items = registry_toc[letter] if letter in registry_toc else []
                current_y = 4
                page_id = 0

                current_page = self.__get_titlepage(document_id, page_id, f'{self.TOC_TITLE} ({letter})', target_directory)

                first_item = True
                for description, link_id in items:
                    if not first_item:
                        # traverse pages, adding as needed
                        if current_y >= 20:
                            current_y = 3
                            if page_id < 99:
                                current_page.save()
                                ZXPage_Token(parent=document, zxtoken_path=current_page.document_path.name, export_format='TKN')

                                page_id += 1
                                current_page = self.__get_page(document_id, page_id, target_directory)
                            else:
                                self.logger.error(f'Item count for letter {letter} was truncated')
                                break
                        else:
                            current_y += 1
                    else:
                        first_item = False

                    current_page.set_string(1, current_y, self.__pad_entry(description))
                    current_page.set_string(27, current_y, link_id, char_attribute=ZXScreen.to_attribute(ink=ZXScreen.CYAN))

                current_page.save()
                ZXPage_Token(parent=document, zxtoken_path=current_page.document_path.name, export_format='TKN')

                document.save()
                document.export(self.output_path, self.registry, sync_registry=False)

        self.registry.save()

    def __pad_entry(self, string, max_length = 25):
        string = string[0:max_length]
        if len(string) < (max_length - 1):
            return (string + ' ').ljust(max_length, '.')
        return string

    def __create_toc_index(self, document_id):
        target_directory = self.__create_path(document_id, 'TOC-Index')

        with self.__get_document(document_id, self.TOC_TITLE, self.TOC_ABBREVIATION, target_directory) as document:
            document.link_a = 1000

            with self.__get_titlepage(document_id, 0, self.TOC_TITLE, target_directory) as page:
                page.set_string(1, 5, 'The corresponding pages have  ')
                page.set_string(1, 6, 'been generated based on TeleZX')
                page.set_string(1, 7, 'registry.')

                start_y = 10
                current_x = 2
                current_y = start_y
                for number, letter in enumerate(self.registry.LETTERS_AZ):
                    page.set_string(current_x, current_y, f'[{letter}]', ZXScreen.to_attribute(ink=ZXScreen.GREEN))
                    page.set_string(current_x + 4, current_y, utilities.format_padded_id(document_id + number + 1), ZXScreen.to_attribute(ink=ZXScreen.CYAN))

                    current_y += 1
                    if current_y > (start_y + 8):
                        current_y = start_y
                        current_x += 10
                page.save()

            # Add reference to created token page
            ZXPage_Token(parent=document, zxtoken_path=page.document_path.name, export_format='TKN')

            # Save and export
            document.save()
            document.export(self.output_path, self.registry, sync_registry=True)

    def __get_document(self, document_id, description, abbreviation, target_directory):
        return ZXDocument(
            document_path=target_directory / "{}{}".format(
                utilities.format_padded_id(document_id),
                ZXDocument.EXTENSION_DOCUMENT
            ),
            document_id=document_id,
            description=description,
            abbreviation=abbreviation
        )

    def __get_page(self, document_id, page_id, target_directory) -> ZXToken:
        return self.__load_frame(
            'frame_default',
            self.__page_path(document_id, page_id, target_directory)
        )

    def __get_titlepage(self, document_id, page_id, page_title, target_directory) -> ZXToken:
        page_title = page_title[0:(ZXScreen.SCREEN_WIDTH_CHARS-2)]
        zx_token = self.__load_frame(
            'frame_default_title',
            self.__page_path(document_id, page_id, target_directory)
        )
        zx_token.set_string(self.__centered_position(page_title), 2, page_title)
        return zx_token

    def __centered_position(self, title):
        return (ZXScreen.SCREEN_WIDTH_CHARS - len(title)) // 2

    def __create_path(self, document_id, path_hint):
        directory = self.documents_path / utilities.suggest_document_name(document_id, path_hint)
        directory.mkdir(exist_ok=True)
        return directory

    def __page_path(self, document_id, page_id, target_directory):
        return target_directory / "{}.{}{}".format(
            utilities.format_padded_id(document_id),
            utilities.format_padded_id(page_id, width=2),
            ZXToken.FILE_EXTENSION
        )

    def __load_frame(self, frame_name, page_path: Path):
        zx_token = ZXToken.from_file(Path(self.documents_path) / 'assets' / f'{frame_name}{ZXToken.FILE_EXTENSION}')
        zx_token.set_document(page_path)
        return zx_token

def print_repository_details(repository: Path):
    print(f'Repository: {repository.resolve()}')

def cmd_export(args, parser):
    repository: Path = Path(args.repository)
    print_repository_details(repository)

    documents_path: Path = repository / 'src'
    documents_path.mkdir(exist_ok=True)
    output_path: Path = repository / 'out'
    output_path.mkdir(exist_ok=True)

    registry_path = repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
    registry = ZXRegistry.from_file(registry_path)

    if args.id:
        print(f'Export document IDs: {','.join(str(x) for x in args.id)}')
        for document_id in args.id:
            __export_id(
                document_id, 
                documents_path, 
                output_path,
                registry)

    if args.start or args.end:
        start_at = args.start if args.start else ZXDocument.DOCUMENT_ID_MIN
        stop_at = args.end if args.end else ZXDocument.DOCUMENT_ID_MAX
        print(f'Export document IDs: {start_at}..{stop_at}')
        for document_id in ZXDocument.scan_documents(documents_path, min_id=start_at, max_id=stop_at):
            __export_id(
                document_id, 
                documents_path, 
                output_path,
                registry)

    registry.save()
    print('Registry saved.')

def __export_id(document_id, documents_path, output_path, registry):
    try:
        document = ZXDocument.from_id(document_id, documents_path)
        document.export(output_directory=output_path, registry=registry)
    except FileNotFoundError:
        print('ERROR:', f'ID {document_id} did not correspond to a file')

def cmd_registry(args, parser):
    repository: Path = Path(args.repository)
    print_repository_details(repository)

    registry_path = repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
    registry = ZXRegistry.from_file(registry_path, allow_create=True)
    if args.clear:
        print('Registry cleared.')
        registry.clear()
    registry.save()
    print('Registry saved.')

def cmd_toc(args, parser):
    print_repository_details(args.repository)
    TOCGenerator(
        repository=args.repository
    ).create_toc()

def main():
    parser = ArgumentParser()
    parser.description = '''
    Tools to generate TeleZX content such as index pages.
    '''
    parser.add_argument('-v', '--version', action='version', version=VERSION, help="Show version information")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug statements")
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_toc = subparsers.add_parser('toc', help='Table of contents')
    parser_toc.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_toc.set_defaults(function=cmd_toc)

    parser_export = subparsers.add_parser('export', help='Export pages')
    parser_export.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_export.add_argument('-s', '--start', type=utilities.argument_is_id, help="First Document ID in export range")
    parser_export.add_argument('-e', '--end', type=utilities.argument_is_id, help="Last Document ID in export range")
    parser_export.add_argument('-i', '--id', type=utilities.argument_is_id, action='extend', nargs='*', help="Specific Document ID to be exported")
    parser_export.set_defaults(function=cmd_export)

    parser_registry = subparsers.add_parser('registry', help='Create registry')
    parser_registry.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_registry.add_argument('-c', '--clear', action='store_true', help="Clear contents")
    parser_registry.set_defaults(function=cmd_registry)

    args = parser.parse_args()
    if args.debug:
        ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

    if 'function' in args:
        args.function(args, parser)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
