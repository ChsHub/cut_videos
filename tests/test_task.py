from cut_videos.model.task import *
from hypothesis import given

def test___init__( gui):
    Task(None)


def test_run():
    Task(None).run()


def test__set_current_frames( value):
    pass


def test__set_total_frames( value):
    pass


def test__run_command( file, command, new_file, input_framerate=''):
    pass


def test_move_files( temp_path, files, reverse):
    pass


def test__convert( i_file, o_file, input_framerate=''):
    pass


def test_convert_gif( o_file, i_file, input_framerate=''):
    pass


if __name__ == '__main__':
    test___init__()