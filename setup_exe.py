from logging import info
from pathlib import Path

from logger_default import Logger
from timerpy import Timer
from utility.setup_lib import setup_exe

__version__ = '2.0.5'
app_name = 'Cut Videos'


def make_exe():
    """
    Compile project files into .exe
    """
    with Timer('Compile exe', log_function=info):
        setup_exe(main_path=Path('__main__.py'),
                  app_name=f'{app_name} {__version__}',
                  icon_path=Path('icon.ico'),
                  dir_option=True,
                  resource_paths=(('.', '.ico'),),
                  pyinstaller_path=Path("C:\\Python38\\Scripts\\pyinstaller.exe"),
                  )


if __name__ == '__main__':
    with Logger():
        make_exe()
