#!/usr/bin/python3
from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities, VERSION
from lib.generate import TOCGenerator

def print_repository_details(repository: Path):
    '''
    Print details for the repository we're working with, nothing interesting to
    see here until I can think of something more suitable.
    '''
    print(f'Repository: {repository.resolve()}')

def cmd_assets(args, parser):
    '''
    Handle argumentparser subcommand for assets.
    '''
    repository: Path = Path(args.repository)
    print_repository_details(repository)

    for colour, value, title_value in ZXFrame.frame_colours():
        frame_path = repository / 'src' / 'assets' / f'frame_{colour}{ZXToken.FILE_EXTENSION}'
        frame = ZXFrame.create_frame(frame_path)
        frame.overlay_box(value, title_value)
        frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
        frame.save()

        frame_path = repository / 'src' / 'assets' / f'frame_{colour}_title{ZXToken.FILE_EXTENSION}'
        frame = ZXFrame.create_frame(frame_path)
        frame.overlay_title_box(value, title_value)
        frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
        frame.save()

def cmd_export(args, parser):
    '''
    Handle argumentparser subcommand for export.
    '''
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
    '''
    Handle argumentparser subcommand for registry.
    '''
    repository: Path = Path(args.repository)
    print_repository_details(repository)

    registry_path = repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
    registry = ZXRegistry.from_file(registry_path, allow_create=True)

    if args.set_ignore:
        print(f'Registry will now ignore {utilities.format_padded_id(args.set_ignore)}')
        registry.set_ignored(args.set_ignore, True)

    if args.remove_ignore:
        print(f'Registry will no longer ignore {utilities.format_padded_id(args.remove_ignore)}')
        registry.set_ignored(args.remove_ignore, False)

    if args.clear:
        print('Registry cleared.')
        registry.clear()
    registry.save()
    print('Registry saved.')

def cmd_toc(args, parser):
    '''
    Handle argumentparser subcommand for table of contents.
    '''
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

    parser_assets = subparsers.add_parser('assets', help='Assets')
    parser_assets.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_assets.set_defaults(function=cmd_assets)

    parser_export = subparsers.add_parser('export', help='Export pages')
    parser_export.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_export.add_argument('-s', '--start', type=utilities.argument_is_id, help="First Document ID in export range")
    parser_export.add_argument('-e', '--end', type=utilities.argument_is_id, help="Last Document ID in export range")
    parser_export.add_argument('-i', '--id', type=utilities.argument_is_id, action='extend', nargs='*', help="Specific Document ID to be exported")
    parser_export.set_defaults(function=cmd_export)

    parser_registry = subparsers.add_parser('registry', help='Create registry')
    parser_registry.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_registry.add_argument('--set-ignore', type=utilities.argument_is_id, help="Add document ID to ignored list")
    parser_registry.add_argument('--remove-ignore', type=utilities.argument_is_id, help="Remove document ID from ignored list")
    parser_registry.add_argument('-c', '--clear', action='store_true', help="Clear contents")
    parser_registry.set_defaults(function=cmd_registry)

    parser_toc = subparsers.add_parser('toc', help='Table of contents')
    parser_toc.add_argument('-r', '--repository', type=utilities.argument_is_dir, required=True, help="Set path to repository")
    parser_toc.set_defaults(function=cmd_toc)

    args = parser.parse_args()
    if args.debug:
        ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

    if 'function' in args:
        args.function(args, parser)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
