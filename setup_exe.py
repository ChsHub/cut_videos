from subprocess import Popen, run
from utility.os_interface import read_file_data, write_file_data
from utility.setup_lib import get_tuples
from os.path import exists, abspath
from os import listdir

text_view_title = 'cut videos'
icon_path = 'icon.ico'
_main_path = abspath('./__main__.py')

print(listdir('.'))
if not exists(_main_path):
    raise FileNotFoundError

if not exists(text_view_title + ".spec"):
    run('pyinstaller "%s" --noconfirm --onedir --noconsole --name "' % _main_path + text_view_title +
          '" --icon "' + icon_path + '"')

    spec_data = read_file_data(text_view_title + ".spec")
    spec_data = spec_data.replace('datas=[',
                                  'datas=[' + ','.join((get_tuples('./lib', types=''), get_tuples('.', types=['.ico']))))

    write_file_data(".", text_view_title + ".spec", spec_data)

run('pyinstaller "' + text_view_title + '.spec"  --noconfirm')