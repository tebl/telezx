#!python3
from argparse import ArgumentParser
import ttkbootstrap as ttk
from lib import ZXEditor

def main():
    parser = ArgumentParser()
    parser.description = '''
    Editor used to edit ZXToken-pages. These reflect the internal memory
    organization of the ZX Spectrum video memory, and can therefore either
    be exported directly to an SCR-file or transcoded into a SPECSCII file.
    '''
    parser.add_argument('-v', '--version', action='store_true', help="Show version information")
    parser.add_argument('-t', '--themename', help="Specify theme")
    parser.add_argument('--list-themes', action='store_true', help="List theme options")
    parser.add_argument('path', nargs='?', help='Specify zxtoken-file to open')

    args = parser.parse_args()
    if args.version:
        about()

    app = ttk.Window(ZXEditor.PROGRAM_TITLE, themename='darkly')
    if args.list_themes:
        list_themes(app)
    if args.themename:
        if args.themename in app.style.theme_names():
            app.style.theme_use(args.themename)
        else:
            print('WARNING: Invalid themename', args.themename)
    zx_editor = ZXEditor(app)
    if args.path:
        try:
            zx_editor.load_file(args.path)
        except ValueError as e:
            print('ERROR: File', e)
            exit(1)
        except FileNotFoundError as e:
            print('ERROR:', f'File {args.path} does not exist')
            exit(1)
    app.protocol("WM_DELETE_WINDOW", lambda app=app: zx_editor.on_quit(app))
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass

def about():
    print(ZXEditor.PROGRAM_TITLE)
    print(ZXEditor.PROGRAM_COPYRIGHT)
    print()
    print(ZXEditor.PROGRAM_LICENSE)
    exit(0)

def list_themes(app):
    for theme in app.style.theme_names():
        print(theme)
    exit(0)

if __name__ == "__main__":
    main()
