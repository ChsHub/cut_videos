from os.path import abspath
from shutil import copy

from utility.setup_lib import setup_exe

text_view_title = 'cut videos'
icon_path = 'icon.ico'
_main_path = abspath('./__main__.py')
setup_exe(main_path=_main_path, app_name=text_view_title, resource_paths=[('lib', '')],
          pyinstaller_path="C:\Python\Python38-32\Scripts\pyinstaller.exe")
