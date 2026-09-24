#!python3
import subprocess, sys
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError, Action
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXRegistry, ZXRegistryTag, ZXLogger, utilities, VERSION
from lib.convert import ATRConverter, TKNConverter, ZXTokenConverter

def cmd_53c(args, parser: ArgumentParser):
    path_out = __get_path_out(args, parser, ZXTokenConverter.get_export_suffixes(include_period=True, include_text=False))
    print(f'Convert {args.input_file} -> {path_out}:')
    converter: ZXTokenConverter = ATRConverter.import_from(args.input_file)
    converter.export_to(path_out)
    print('Done.')

def cmd_zx_token(args, parser: ArgumentParser):
    path_out = __get_path_out(args, parser, ZXTokenConverter.get_export_suffixes(include_period=True))
    print(f'Convert {args.input_file} -> {path_out}:')
    converter: ZXTokenConverter = ZXTokenConverter.open(args.input_file)
    converter.export_to(path_out)
    print('Done.')

def __get_path_out(args, parser: ArgumentParser, extensions: list[str]) -> Path:
    path_out: Path = Path(args.output_file) if args.output_file else None
    if path_out:
        if path_out.suffix not in extensions:
            parser.error(f'Invalid file extension: {path_out.suffix}')
    else:
        path_out = Path(args.input_file).with_suffix(f'.{args.output_format}')
    if args.input_file == path_out:
        parser.error('Input file and output file can\'t be the same')
    return path_out

def main():
    parser = ArgumentParser()
    parser.description = '''
    Tools to convert TeleZX-related content
    '''
    parser.add_argument('-v', '--version', action='version', version=VERSION, help="Show version information")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug statements")
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_atr = subparsers.add_parser('53c', help='ATR (53c)')
    parser_atr.add_argument('-i', '--input-file', type=utilities.argument_is_file, required=True)
    parser_atr.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_atr.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(include_period=False, include_text=False), default='zxtoken', help='Specify output format when output-file not used')
    parser_atr.set_defaults(function=cmd_53c)

    parser_zx_token = subparsers.add_parser('zx_token', help='TeleZX (ZXToken)')
    parser_zx_token.add_argument('-i', '--input-file', type=utilities.argument_is_file, required=True)
    parser_zx_token.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_zx_token.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(include_period=False), default='zxtoken', help='Specify output format when output-file not used')
    parser_zx_token.set_defaults(function=cmd_zx_token)

    args = parser.parse_args()
    if args.debug:
        ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

    if 'function' in args:
        args.function(args, parser)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
