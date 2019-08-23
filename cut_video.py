import sys
from io import StringIO
from logging import info
from re import findall
from shutil import move
from subprocess import run, Popen
from tempfile import TemporaryDirectory

from os.path import join
from utility.logger import Logger
from utility.os_interface import exists, make_directory, get_absolute_path
from utility.path_str import get_clean_path
from utility.timer import Timer
from utility.utilities import get_file_type, remove_file_type, is_file_type
from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font
from wx import Frame, ID_ANY, App, EXPAND, HORIZONTAL, EVT_CLOSE, CheckBox, Icon, Bitmap, \
    BITMAP_TYPE_ANY
from wx import NORMAL, MODERN
from wx import TextCtrl
from wxwidgets import FileInput, SimpleButton

class StandardSelection(Panel):
    def __init__(self, parent, callback, title, options):
        super().__init__(parent)

        sizer = BoxSizer(VERTICAL)
        text = StaticText(self, label=title)
        sizer.Add(text)
        self.selection = ComboBox(self, style=CB_DROPDOWN | CB_READONLY, choices=options)
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        text.SetFont(font)
        self.selection.SetFont(font)
        # self.selection.SetFont(font)
        self.selection.SetValue(options[0])
        if callback:
            self.selection.Bind(EVT_TEXT, lambda x: callback(self.selection.GetValue()))
        sizer.Add(self.selection, 1, EXPAND)
        self.SetSizer(sizer)

    def get_selection(self):
        return self.selection.GetValue()


class SimpleInput(Panel):

    def __init__(self, parent, label, initial=""):
        super().__init__(parent)

        sizer = BoxSizer(HORIZONTAL)
        self._text_input = TextCtrl(self)

        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        self._text_input.SetFont(font)
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input, 1, EXPAND)

        text = StaticText(self, label=label)
        text.SetFont(font)
        sizer.Add(text, 1, EXPAND)
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()


class MyForm(Frame):
    _files = []
    _path = None
    _start = None
    _end = None
    _ffmpeg_path = get_absolute_path('lib\\ffmpeg\\bin\\ffmpeg.exe')
    _frame_format = '.png'

    def __init__(self):

        if not exists(self._ffmpeg_path):
            info('ffmpeg not found')
            raise FileNotFoundError

        # init window
        Frame.__init__(self, None, ID_ANY, "CUT", size=(800, 800))
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        loc = Icon()
        loc.CopyFromBitmap(Bitmap('icon.ico', BITMAP_TYPE_ANY))
        self.SetIcon(loc)
        panel = Panel(self, EXPAND)
        sizer = BoxSizer(VERTICAL)

        sizer.Add(FileInput(panel, text_button="Open File", callback=self._set_target,
                            file_type="*.mkv;*.mp4;*.webm;*.avi;*.bmp;*.gif;*.png;*.jpg",
                            text_title="OPEN", text_open_file="File"), 1, EXPAND)

        #  Create Input fields
        self._start_input = SimpleInput(panel, label='START', initial='00:00:00.0')

        self._end_input = SimpleInput(panel, label='END', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='33')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='24')

        # Create check inputs
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        self._check_webm = CheckBox(panel, label="WEBM")
        self._check_webm.SetFont(font)
        self._check_mp4 = CheckBox(panel, label="MP4")
        self._check_mp4.SetFont(font)
        self._check_frames = CheckBox(panel, label="FRAMES")
        self._check_frames.SetFont(font)
        self._check_gif = CheckBox(panel, label="gif")
        self._check_gif.SetFont(font)

        self._audio_options = {'Native format': '-c:a copy', 'no audio': '-an', 'opus': '-c:a libopus -vbr on -b:a 128k'}
        self._audio_select = StandardSelection(parent=panel, options=list(self._audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        # Add inputs to sizer
        sizer.Add(self._start_input, 1, EXPAND)
        sizer.Add(self._end_input, 1, EXPAND)
        sizer.Add(self._scale_input, 1, EXPAND)
        sizer.Add(self._webm_input, 1, EXPAND)
        sizer.Add(self._framerate_input, 1, EXPAND)

        sizer.Add(self._audio_select, 1, EXPAND)
        sizer.Add(self._check_webm, 1, EXPAND)
        sizer.Add(self._check_mp4, 1, EXPAND)
        sizer.Add(self._check_frames, 1, EXPAND)
        sizer.Add(self._check_gif, 1, EXPAND)

        # Add Button, and put everything to the panel
        sizer.Add(SimpleButton(panel, text_button='CUT', callback=self._cut), 1, EXPAND)
        panel.SetSizer(sizer)

    def _set_target(self, path, files):
        self._path = path
        self._files = files

    def _run_command(self, file, command, new_file, time, input_framerate=''):

        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Resolve selected audio codec
        audio = self._audio_options[self._audio_select.get_selection()]

        command = ['"' + self._ffmpeg_path + '"',
                   input_framerate, '-i', '"' + file + '"',
                   time, audio, command,
                   '"' + new_file + '"']
        command = ' '.join(command)
        info(command)
        Popen(command).communicate()

    def move_files(self, temp_path, files, reverse):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)

            if reverse:
                move(join(temp_path, file_name), join(self._path, file))
            else:
                move(join(self._path, file), join(temp_path, file_name))

    def _cut(self, event):

        types = ('.bmp', '.png', '.jpg')
        frames = list(filter(lambda x: is_file_type(x, types), self._files))
        videos = list(filter(lambda x: not is_file_type(x, types), self._files))
        # Load frames
        if len(frames) > 1:
            with TemporaryDirectory(prefix=self._path + '/') as temp_path:
                self.move_files(temp_path, frames, reverse=False)
                # Convert the frames
                input_framerate = ' -framerate ' + self._framerate_input.get_value()
                self._convert(i_file=join(temp_path, '%3d' + get_file_type(frames[0])),
                              o_file=self._path, time='', input_framerate=input_framerate)
                self.move_files(temp_path, frames, reverse=True)
        # no else

        # Load videos
        if len(videos) >= 1:
            # Get time settings
            if self._end_input.get_value() == '00:00:00.0':
                time = ''
            else:
                time = '-sn -ss ' + self._start_input.get_value() + ' -to ' + self._end_input.get_value()

            for i_file in videos:
                # Get output file name
                o_file = join(self._path, '_' + (self._start_input.get_value() + '_' +
                                                 self._end_input.get_value()).replace(":", "-")
                              + '_' + remove_file_type(i_file))
                # Convert the video
                self._convert(join(self._path, i_file), o_file, time)
        # no else

    def _convert(self, i_file, o_file, time, input_framerate=''):

        if self._check_webm.GetValue():
            self.convert_webm(o_file, i_file, time, input_framerate=input_framerate)

        if self._check_mp4.GetValue():
            self.convert_mp4(o_file, i_file, time, input_framerate=input_framerate)

        if self._check_frames.GetValue():
            with Timer('FRAMES'):
                self.convert_frames(o_file, i_file, time, input_framerate=input_framerate)

        if self._check_gif.GetValue():
            with Timer('GIF'):
                self.convert_gif(o_file, i_file, time, input_framerate=input_framerate)

        info('\nDONE')

    def convert_webm(self, o_file, i_file, time, input_framerate=''):
        o_file += ".webm"
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        command = ' -lavfi "scale=' + self._scale_input.get_value() + '" -c:v libvpx-vp9 -speed 0 -crf ' + self._webm_input.get_value() + \
                  ' -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 ' \
                  '-auto-alt-ref 1 -lag-in-frames 25'

        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file,
                          time=time, input_framerate=input_framerate)

    def convert_mp4(self, o_file, i_file, time, input_framerate=''):
        o_file += ".mp4"

        self._run_command(file=i_file,
                          command='-async 1 -lavfi "scale=' + self._scale_input.get_value() + '"',
                          new_file=o_file,
                          time=time, input_framerate=input_framerate)

    def convert_gif(self, o_file, i_file, time, input_framerate=''):

        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer('GENERATE PALETTE'):
                palette = palette_dir + '/palette.png'
                self._run_command(file=i_file,
                                  command=' -vf "scale=' + self._scale_input.get_value() + ':flags=lanczos,palettegen"',
                                  new_file=palette,
                                  time=time, input_framerate=input_framerate)
            if not exists(palette):
                info('No Palette')
                return

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"',
                              new_file=o_file + "_bayer.gif",
                              time=time, input_framerate=input_framerate)

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=none"',
                              new_file=o_file + "_none.gif",
                              time=time, input_framerate=input_framerate)

            self._run_command(file=i_file,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + '"',
                              new_file=o_file + '_no_pal.gif',
                              time=time, input_framerate=input_framerate)

    def convert_frames(self, o_file, i_file, time, input_framerate=''):
        # o_file is output directory for frames
        if exists(o_file):
            info('Exists')
            return
        make_directory(o_file)
        o_file = get_clean_path(join(o_file, "%03d" + self._frame_format))
        self._run_command(file=i_file,
                          command='',
                          new_file=o_file,
                          time=time, input_framerate=input_framerate)


if __name__ == "__main__":
    with Logger(debug=True):
        app = App(False)
        frame = MyForm()
        frame.Show()
        app.MainLoop()
