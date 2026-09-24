#!python3
import subprocess, sys
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError, Action
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXRegistry, ZXRegistryTag, ZXLogger, utilities, VERSION
from lib.convert import ATRConverter, TKNConverter, ZXTokenConverter

def cmd_53c(args, parser: ArgumentParser):
    path_out: Path = Path(args.output_file) if args.output_file else None
    if path_out:
        if path_out.suffix not in ZXTokenConverter.get_export_suffixes():
            parser.error(f'Unknown file extension: {path_out.suffix}')
    else:
        path_out = Path(args.input_file).with_suffix(f'.{args.output_format}')

    print(f'Convert {args.input_file} -> {path_out}:')
    converter: ZXTokenConverter = ATRConverter.import_from(args.input_file)
    converter.export_to(path_out)

    print('Done.')

def main():
    parser = ArgumentParser()
    parser.description = '''
    Tools to convert TeleZX-related content
    '''
    parser.add_argument('-v', '--version', action='version', version=VERSION, help="Show version information")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug statements")
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_assets = subparsers.add_parser('53c', help='Manage assets')
    parser_assets.add_argument('-i', '--input-file', type=utilities.argument_is_file, required=True)
    parser_assets.add_argument('-o', '--output-file', type=str)
    parser_assets.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(strip_period=True), default='zxtoken')
    parser_assets.set_defaults(function=cmd_53c)

    args = parser.parse_args()
    if args.debug:
        ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

    if 'function' in args:
        args.function(args, parser)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
