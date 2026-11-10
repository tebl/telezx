#!python3
import subprocess, sys
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError, Action
from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage, ZXPage_Overlay, ZXPage_Token, ZXRegistry, ZXRegistryTag, ZXLogger, utilities
from lib.convert import ATRConverter, S81Converter, SCRConverter, TKNConverter, ZXTokenConverter

def cmd_53c(args, parser: ArgumentParser):
    __check_args(args, parser)
    for input in args.input_file:
        path_out = __get_path_out(args, parser, input, ZXTokenConverter.get_export_suffixes(leading_period=True, include_text=False))
        print(f'Convert {input} -> {path_out}:')
        converter: ZXTokenConverter = ATRConverter.import_from(args.input_file)
        converter.export_to(path_out)
    print('Done.')

def __check_args(args, parser: ArgumentParser):
    if args.output_file and len(args.input_file) > 1:
        parser.error('Specified output file when using multiple inputs')

def cmd_s81(args, parser: ArgumentParser):
    __check_args(args, parser)
    for input in args.input_file:
        path_out = __get_path_out(args, parser, input, ZXTokenConverter.get_export_suffixes(leading_period=True, include_text=False))
        print(f'Convert {input} -> {path_out}:')
        converter: ZXTokenConverter = S81Converter.import_from(input)
        converter.export_to(path_out)

def cmd_scr(args, parser: ArgumentParser):
    __check_args(args, parser)
    for input in args.input_file:
        path_out = __get_path_out(args, parser, input, ZXTokenConverter.get_export_suffixes(leading_period=True, include_text=False))
        print(f'Convert {input} -> {path_out}:')
        converter: ZXTokenConverter = SCRConverter.import_from(input)
        converter.export_to(path_out)
    print('Done.')

def cmd_zx_token(args, parser: ArgumentParser):
    __check_args(args, parser)
    for input in args.input_file:
        path_out = __get_path_out(args, parser, input, ZXTokenConverter.get_export_suffixes(leading_period=True))
        print(f'Convert {input} -> {path_out}:')
        converter: ZXTokenConverter = ZXTokenConverter.open(input)
        converter.export_to(path_out)
    print('Done.')

def __get_path_out(args, parser: ArgumentParser, input: Path, extensions: list[str]) -> Path:
    path_out: Path = Path(args.output_file) if args.output_file else None
    if path_out:
        if path_out.suffix not in extensions:
            parser.error(f'Invalid file extension: {path_out.suffix}')
    else:
        path_out = Path(input).with_suffix(f'.{args.output_format}')
    if input == path_out:
        parser.error('Input file and output file can\'t be the same')
    return path_out

def main():
    parser = ArgumentParser()
    parser.description = '''
    Tools to convert TeleZX-related content
    '''
    parser.add_argument('-v', '--version', action='version', version=utilities.get_version(), help="Show version information")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug statements")
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_atr = subparsers.add_parser('53c', help='ATR (53c)')
    parser_atr.add_argument('-i', '--input-file', type=utilities.argument_is_file, nargs='*', required=True)
    parser_atr.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_atr.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(leading_period=False, include_text=False), default='zxtoken', help='Specify output format when output-file not used')
    parser_atr.set_defaults(function=cmd_53c)

    parser_s81 = subparsers.add_parser('s81', help='S81 (ZX81)')
    parser_s81.add_argument('-i', '--input-file', type=utilities.argument_is_file, nargs='*', required=True)
    parser_s81.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_s81.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(leading_period=False, include_text=False), default='zxtoken', help='Specify output format when output-file not used')
    parser_s81.set_defaults(function=cmd_s81)

    parser_s81 = subparsers.add_parser('scr', help='SCR (Screenshot)')
    parser_s81.add_argument('-i', '--input-file', type=utilities.argument_is_file, nargs='*', required=True)
    parser_s81.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_s81.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(leading_period=False, include_text=False), default='zxtoken', help='Specify output format when output-file not used')
    parser_s81.set_defaults(function=cmd_scr)

    parser_zx_token = subparsers.add_parser('zxtoken', help='TeleZX (ZXToken)')
    parser_zx_token.add_argument('-i', '--input-file', type=utilities.argument_is_file, nargs='*', required=True)
    parser_zx_token.add_argument('-o', '--output-file', type=str, help='Specify output path (extension dictates format)')
    parser_zx_token.add_argument('-f', '--output-format', choices=ZXTokenConverter.get_export_suffixes(leading_period=False), default='zxtoken', help='Specify output format when output-file not used')
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
