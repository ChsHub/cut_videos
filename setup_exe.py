from subprocess import Popen
from utility.os_interface import read_file_data, write_file_data, exists
from utility.setup_lib import get_tuples

text_view_title = 'reaction videos'
icon_path = 'icon.ico'

if not exists(text_view_title + ".spec"):
    Popen('pyinstaller "cut_videos/cut_video.py"  --noconfirm --onedir --noconsole --name "' + text_view_title +
          '" --icon "' + icon_path + '"').communicate()

    spec_data = read_file_data(text_view_title + ".spec")
    spec_data = spec_data.replace('datas=[',
                                  'datas=[' + ','.join((get_tuples('./lib', types=''), get_tuples('.', types=['.ico']))))

    write_file_data(".", text_view_title + ".spec", spec_data)

Popen('pyinstaller "' + text_view_title + '.spec"  --noconfirm').communicate()