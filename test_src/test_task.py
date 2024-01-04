from hypothesis.strategies import integers

from src.model.task import *
from hypothesis import given

from src.model.task import _format_time


def test___init__(gui):
    Task(None)


def test_run():
    Task(None).run()


def test__set_current_frames(value):
    pass


def test__set_total_frames(value):
    pass


def test__run_command(file, command, new_file, input_framerate=''):
    pass


def test_move_files(temp_path, files, reverse):
    pass


def test__convert(i_file, o_file, input_framerate=''):
    pass


def test_convert_gif(o_file, i_file, input_framerate=''):
    pass


@given(integers(min_value=1, max_value=9))
def test_unformat_time(d):
    assert '00000000' == unformat_time('')
    assert '00250000' == unformat_time('25-')
    assert '02000000' == unformat_time('2--')
    assert '90000000' == unformat_time('90--')
    assert '0000%s000' % d == unformat_time('%s0' % d)
    assert '00000%s00' % d == unformat_time('%s' % d)
    assert '00%s00000' % d == unformat_time('%s0-' % d)
    assert '000%s0000' % d == unformat_time('%s-' % d)

    assert '00000010' == unformat_time('.1')
    assert '00000001' == unformat_time('.01')


@given(integers(min_value=1, max_value=9))
def test__format_time(d):
    assert _format_time('00:00:00.0') == ''
    assert _format_time('00:25:00.0') == '25-'
    assert _format_time('02:00:00.0') == '2--'
    assert _format_time('90:00:00.0') == '90--'
    assert _format_time('00:00:%s0.0' % d) == '%s0' % d
    assert _format_time('00:00:0%s.0' % d) == '%s' % d
    assert _format_time('00:%s0:00.0' % d) == '%s0-' % d
    assert _format_time('00:0%s:00.0' % d) == '%s-' % d

    assert _format_time('00:00:00.002') == '.002'
    assert _format_time('00:00:00.100') == '.1'
    assert _format_time('00:00:00.010') == '.01'


if __name__ == '__main__':
    test_unformat_time()
    test__format_time()
