#!/usr/bin/python3
import subprocess
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities, VERSION
from lib.generate import AssetHelper, DocumentHelper, TOCHelper, TransformationHelper, TransformationFormatError

def cmd_assets(args, parser):
    '''
    Handle argumentparser subcommand for assets.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)

    helper = AssetHelper(repository)
    if args.create_frames:
        helper.create_frames()
    print('Done.')

def cmd_documents(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for managing documents and their
    various properties. Specifying a document_id of 0 for links will
    clear the current values. A link should not have a text without a
    valid document ID.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    registry = get_registry(repository)
    changes = False

    helper = DocumentHelper(repository)
    if args.create_id:
        try:
            document = helper.create_document(args.create_id, args.path_hint)
            print_document_details(document, registry, action='created')
        except FileExistsError:
            print(f'ERROR: Document with ID {args.create_id} already exists!')
            return

    if args.open_id:
        try:
            document = helper.open_document(args.open_id, allow_none=False)
            print_document_details(document, registry, action='opened')
        except FileNotFoundError:
            print(f'ERROR: Document with ID {args.open_id} could not be loaded!')
            return

    # Update document properties
    if __update_document(document, args):
        changes = True
        document.save()
    print()

    # Print document again if there were changes
    if changes:
        print_document_details(document, registry, 'changed')

    print('Done.')

def __update_document(document, args) -> bool:
    changes = False
    if args.set_description is not None:
        changes = True
        document.description = None if args.set_description == '' else args.set_description
    if args.set_abbreviation is not None:
        changes = True
        document.abbreviation = None if args.set_abbreviation == '' else args.set_abbreviation

    if args.set_link_a is not None:
        changes = True
        if args.set_link_a == 0:
            document.link_a = None
            document.link_a_txt = None
        else:
            document.link_a = args.set_link_a
            document.link_a_txt = args.set_link_a_txt if args.set_link_a_txt else None
    elif args.set_link_a_txt:
        changes = True
        document.link_a_txt = args.set_link_a_txt

    if args.set_link_b is not None:
        changes = True
        if args.set_link_b == 0:
            document.link_b = None
            document.link_b_txt = None
        else:
            document.link_b = args.set_link_b
            document.link_b_txt = args.set_link_b_txt if args.set_link_b_txt else None
    elif args.set_link_b_txt:
        changes = True
        document.link_b_txt = args.set_link_b_txt

    if args.set_link_c is not None:
        changes = True
        if args.set_link_c == 0:
            document.link_c = None
            document.link_b_txt = None
        else:
            document.link_c = args.set_link_c
            document.link_c_txt = args.set_link_c_txt if args.set_link_c_txt else None
    elif args.set_link_c_txt:
        changes = True
        document.link_c_txt = args.set_link_c_txt
    return changes

def cmd_export(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for export.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    registry = get_registry(repository)

    documents_path: Path = repository / 'src'
    documents_path.mkdir(exist_ok=True)
    output_path: Path = repository / 'out'
    output_path.mkdir(exist_ok=True)

    registry = get_registry(repository)
    if args.id:
        print(f'Export document IDs: {','.join(str(x) for x in args.id)}')
        for document_id in args.id:
            __export_id(
                repository,
                document_id, 
                output_path,
                registry)

    if args.all or args.start or args.end:
        start_at = args.start if args.start else ZXDocument.DOCUMENT_ID_MIN
        stop_at = args.end if args.end else ZXDocument.DOCUMENT_ID_MAX
        print(f'Export document IDs: {start_at}..{stop_at}')
        for document_id in ZXDocument.scan_documents(repository, min_id=start_at, max_id=stop_at):
            __export_id(
                repository,
                document_id, 
                output_path,
                registry)

    registry.save()
    print('Registry saved.')

def __export_id(repository: Path, document_id: int, output_path, registry):
    try:
        document = ZXDocument.from_document_id(repository, document_id)
        document.export(output_directory=output_path, registry=registry)
    except FileNotFoundError:
        print('ERROR:', f'ID {document_id} did not correspond to a file')

def cmd_pages(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for managing document pages.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    registry = get_registry(repository)
    changes = False

    helper = DocumentHelper(repository)
    if args.document_id:
        try:
            document = helper.open_document(args.document_id, allow_none=False)
            print_document_details(document, registry, action='opened')
        except FileNotFoundError:
            print(f'ERROR: Document with ID {args.document_id} could not be loaded!')
            return
    print()

    page = None
    if args.create_text:
        page = helper.create_text(document, args.with_frame)
        print_page_details(page, 'created')
        changes = True

    if args.create_token:
        page = helper.create_token(document, args.with_frame, args.with_format)
        print_page_details(page, 'created')
        changes = True

    if args.create_overlay:
        scr_about = ZXPage_Overlay.blank_about()
        scr_about['title'] = args.set_scr_title if args.set_scr_title else __suggest_scr_title(args.create_overlay)
        scr_about['author'] = args.set_scr_author
        scr_about['source'] = args.set_scr_source if args.set_scr_source else __suggest_scr_source(args.create_overlay)
        scr_about['license'] = args.set_scr_license
        page = helper.create_overlay(document, args.create_overlay, scr_about, path_hint=args.path_hint)
        print_page_details(page, 'created')
        changes = True

    if args.copy_token:
        page = helper.copy_token(document, args.copy_token, args.with_format)
        print_page_details(page, 'created')
        changes = True

    if args.link_token:
        page = helper.link_token(document, args.link_token.resolve(), args.with_format)
        print_page_details(page, 'created')
        changes = True

    if args.page_id is not None:
        page = document.get_page(args.page_id)
        if not page:
            print(f'ERROR: Page with ID {args.page_id} could not be loaded!')
            return
        print_page_details(page, 'opened')

    # A page should previously have been created or opened
    if not page:
        parser.error('No page loaded!')

    if __update_page(args, parser, document, page):
        changes = True
        document.save()
    print()

    # Print changes
    if changes:
        print_document_details(document, registry, 'changed')

    # Open up asset editor if requested
    if args.editor:
        print('Opening asset editor:')
        __open_editor(args, parser, page)

    # Export document upon request
    if args.export:
        print('Exporting document:')
        helper.export_document(document, registry)
        registry.save()

    print('Done.')

def __suggest_scr_source(asset_path: Path):
    return asset_path.name

def __suggest_scr_title(asset_path: Path):
    return asset_path.stem.replace('_', ' ')

def __update_page(args, parser: ArgumentParser, document: ZXDocument, page: ZXPage) -> bool:
    # Not really implemented as most tasks are just easier to perform by
    # editing files directly. Sorry about that.
    return False

def __open_editor(args, parser: ArgumentParser, page: ZXPage):
    if isinstance(page, ZXPage_Token):
        subprocess.run([utilities.get_project_root() / 'editor.py', page.zxtoken_path])
        return
    parser.error(f'No asset editor for {page}')

def cmd_registry(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for registry.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    registry = get_registry(repository)
    print()

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

def cmd_toc(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for table of contents.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    print()

    helper = TOCHelper(args.repository)
    if args.update:
        print('Updating TOC:')
        helper.create_toc()
    print('Done.')

def cmd_transform(args, parser: ArgumentParser):
    '''
    Handle argumentparser subcommand for transforming document pages.
    '''
    repository: Path = get_repository(args.repository, parser)
    print_repository_details(repository)
    registry = get_registry(repository)
    changes = False

    helper = TransformationHelper(repository)
    if args.document_id:
        try:
            document = helper.open_document(args.document_id, allow_none=False)
            print_document_details(document, registry, action='opened')
        except FileNotFoundError:
            print(f'ERROR: Document with ID {args.document_id} could not be loaded!')
            return
    print()

    if args.page_id is not None:
        page = document.get_page(args.page_id)
        if not page:
            print(f'ERROR: Page with ID {args.page_id} could not be loaded!')
            return

        try:
            helper.open_page(page)
            print_page_details(page, 'opened')
        except TransformationFormatError as e:
            print(f'ERROR: {e}')
            return
        except FileNotFoundError:
            print(f'ERROR: Page with ID {args.page_id} has missing asset')
            return
    print()

    if args.blank_line:
        for char_y in args.blank_line:
            helper.clear_line(char_y)

    if args.restore:
        print('Restoring original file:')
        helper.restore()
        # helper.blank_line
        # if args.id:
        # print(f'Export document IDs: {','.join(str(x) for x in args.id)}')
        # for document_id in args.id:
        #     __export_id(
        #         repository,
        #         document_id, 
        #         output_path,
        #         registry)

    print('Done.')

def get_repository(path: Path, parser: ArgumentParser) -> Path:
    path: Path = Path(path)
    if not path.is_dir():
        parser.error(f'Repository path {path} does not exist!')
    return path

def get_registry(repository: Path, allow_create=True) -> ZXRegistry:
    registry_path = repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
    return ZXRegistry.from_file(registry_path, allow_create)

def print_document_details(document: ZXDocument, registry: ZXRegistry, action=None):
    '''
    Print details for the specified document
    '''
    col_width = 13
    print(f'Document {action}:' if action else f'Document:')
    print_indented('Document ID:'.ljust(col_width), f'{document.document_id}')
    print_indented('Description:'.ljust(col_width), f'{document.description}')
    print_indented('Abbreviation:'.ljust(col_width), f'{document.abbreviation}')
    print_indented('Link A:'.ljust(col_width), __format_link(document.link_a, document.link_a_txt, registry))
    print_indented('Link B:'.ljust(col_width), __format_link(document.link_b, document.link_b_txt, registry))
    print_indented('Link C:'.ljust(col_width), __format_link(document.link_c, document.link_c_txt, registry))

    if document.pages:
        for page_id, page in enumerate(document):
            if page_id == 0:
                print_indented('Pages:'.ljust(col_width), utilities.format_padded_id(page_id, width=2), page)
            else:
                print_indented(''.ljust(col_width), utilities.format_padded_id(page_id, width=2), page)
    else:
        print_indented('Pages:'.ljust(col_width), 'No pages.')

def __format_link(link: int, link_txt: str, registry: ZXRegistry):
    if not link:
        return 'Not set.'
    if not link_txt:
        link_txt = registry.lookup_abbreviation(link)
    if not link_txt:
        link_txt = utilities.format_padded_id(link, width=4)
    return f'{link}, "{link_txt}"'

def print_page_details(page, action=None):
    col_width = 13
    print(f'Page {action}:' if action else f'Page:')
    print_indented('Details:'.ljust(col_width), f'{page}')

def print_repository_details(repository: Path):
    '''
    Print details for the repository we're working with, nothing interesting to
    see here until I can think of something more suitable.
    '''
    print(f'Repository: {repository.resolve()}')

def print_indented(*segments, indent_count=1,):
    print(' '*ZXLogger.INDENT_WIDTH*indent_count, end='')
    if segments:
        for segment in segments:
            print(segment, end=' ')
    print()

def main():
    parser = ArgumentParser()
    parser.description = '''
    Tools to generate TeleZX content such as index pages.
    '''
    parser.add_argument('-v', '--version', action='version', version=VERSION, help="Show version information")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug statements")
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_assets = subparsers.add_parser('assets', help='Manage assets')
    parser_assets.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    group = parser_assets.add_mutually_exclusive_group(required=True)
    group.add_argument('--create-frames', action='store_true', help="Create frames of different colours")
    parser_assets.set_defaults(function=cmd_assets)

    parser_document = subparsers.add_parser('document', help='Manage documents')
    parser_document.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    group = parser_document.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--create-id', type=utilities.argument_is_document_id, help="Create document ID")
    group.add_argument('-f', '--open-id', type=utilities.argument_is_document_id, help="Open document ID")
    group = parser_document.add_argument_group('Document management')
    group.add_argument('--path-hint', type=str, help="Path hint appended to document directory upon creation")
    group.add_argument('--set-abbreviation', type=str, help="Set abbreviation")
    group.add_argument('--set-description', type=str, help="Set description")
    group.add_argument('--set-link-a', type=utilities.argument_is_document_id, help="Set link A")
    group.add_argument('--set-link-a-txt', type=str, help="Set link A description")
    group.add_argument('--set-link-b', type=utilities.argument_is_document_id, help="Set link B")
    group.add_argument('--set-link-b-txt', type=str, help="Set link B description")
    group.add_argument('--set-link-c', type=utilities.argument_is_document_id, help="Set link C")
    group.add_argument('--set-link-c-txt', type=str, help="Set link C description")
    parser_document.set_defaults(function=cmd_documents)

    parser_export = subparsers.add_parser('export', help='Export documents')
    parser_export.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    parser_export.add_argument('-a', '--all', action='store_true', help="Export all documents found")
    parser_export.add_argument('-s', '--start', type=utilities.argument_is_document_id, help="First Document ID in export range")
    parser_export.add_argument('-e', '--end', type=utilities.argument_is_document_id, help="Last Document ID in export range")
    parser_export.add_argument('-i', '--id', type=utilities.argument_is_document_id, action='extend', nargs='*', help="Specific Document ID to be exported")
    parser_export.set_defaults(function=cmd_export)

    parser_page = subparsers.add_parser('page', help='Manage document pages')
    parser_page.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    parser_page.add_argument('-f', '--document-id', type=utilities.argument_is_document_id, required=True, help="Specify document ID")
    group = parser_page.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--page-id', type=utilities.argument_is_page_id, help="Open page ID")
    group.add_argument('--link-token', type=check_zxtoken, help="Link ZXToken as page in document")
    group.add_argument('--copy-token', type=check_zxtoken, help="Copy ZXToken to document")
    group.add_argument('--create-token', action='store_true', help="Add ZXToken page to document")
    group.add_argument('--create-text', action='store_true', help="Add clear text page to document")
    group.add_argument('--create-overlay', type=check_scr, help="Add clear text page to document")
    group = parser_page.add_argument_group('Page properties')
    group.add_argument('--path-hint', type=str, help="Path hint used when creating file")
    group.add_argument('--with-frame', type=check_zxtoken, help="Path to ZXToken to use as a template")
    group.add_argument('--with-format', choices={'SCR', 'TKN'}, default='TKN', help="Format of ZXToken export")
    group.add_argument('--set-scr-title', type=str, default='', help="The SCR about field for title")
    group.add_argument('--set-scr-author', type=str, default='', help="The SCR about field for author")
    group.add_argument('--set-scr-source', type=str, default='', help="The SCR about field for source")
    group.add_argument('--set-scr-license', type=str, default='', help="The SCR about field for license")
    group.add_argument('-e', '--editor', action='store_true', help="Open asset editor")
    group.add_argument('--export', action='store_true', help="Export affected document")
    parser_page.set_defaults(function=cmd_pages)

    parser_registry = subparsers.add_parser('registry', help='Manage registry')
    parser_registry.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    parser_registry.add_argument('--set-ignore', type=utilities.argument_is_document_id, help="Add document ID to ignored list")
    parser_registry.add_argument('--remove-ignore', type=utilities.argument_is_document_id, help="Remove document ID from ignored list")
    parser_registry.add_argument('-x', '--clear', action='store_true', help="Clear contents")
    parser_registry.set_defaults(function=cmd_registry)

    parser_toc = subparsers.add_parser('toc', help='Table of contents')
    parser_toc.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    group = parser_toc.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--update', action='store_true', help="Update TOC from registry")
    parser_toc.set_defaults(function=cmd_toc)

    parser_transform = subparsers.add_parser('transform', help='Transform page contents')
    parser_transform.add_argument('-r', '--repository', type=utilities.argument_is_dir, default=__get_default_repository(), help="Set path to repository")
    parser_transform.add_argument('-f', '--document-id', type=utilities.argument_is_document_id, required=True, help="Specify document ID")
    parser_transform.add_argument('-p', '--page-id', type=utilities.argument_is_page_id, required=True, help="Open page ID")
    group = parser_transform.add_mutually_exclusive_group(required=True)
    group.add_argument('--blank-line', type=utilities.argument_is_page_id, action='extend', nargs='*', help="Clear the specified line")
    group.add_argument('--restore', action='store_true', help="Restore original file")
    parser_transform.set_defaults(function=cmd_transform)

    args = parser.parse_args()
    if args.debug:
        ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

    if 'function' in args:
        args.function(args, parser)
    else:
        parser.print_help()

def check_zxtoken(path: Path) -> Path:
    path = utilities.argument_is_file(path)
    if not path.suffix == ZXToken.FILE_EXTENSION:
        raise ArgumentError('path is not a zxtoken')
    return path

def check_scr(path: Path) -> Path:
    path = utilities.argument_is_file(path)
    if not path.suffix == ZXDocument.EXTENSION_SCR:
        raise ArgumentError('path is not an scr-file')
    return path

def __get_default_repository() -> Path:
    return utilities.get_project_root() / 'repository'

if __name__ == "__main__":
    main()
