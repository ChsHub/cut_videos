from shutil import move
from subprocess import Popen
from tempfile import TemporaryDirectory

from utility.logger import Logger
from utility.os_interface import get_full_path, exists, make_directory, get_absolute_path
from utility.path_str import get_clean_path
from utility.timer import Timer
from utility.utilities import get_file_type, remove_file_type, is_file_type
from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font, Size
from wx import Frame, ID_ANY, App, EXPAND, HORIZONTAL, EVT_CLOSE, CheckBox, Icon, Bitmap, \
    BITMAP_TYPE_ANY
from wx import TextCtrl
from wxwidgets.file_input import FileInput
from wxwidgets.standard_button import StandardButton
from wx import DECORATIVE, ITALIC, NORMAL


class StandardSelection(Panel):
    def __init__(self, parent, callback, title, options):
        super().__init__(parent)

        sizer = BoxSizer(VERTICAL)
        sizer.Add(StaticText(self, label=title))
        self.selection = ComboBox(self, style=CB_DROPDOWN | CB_READONLY, choices=options)
        self.selection.SetValue(options[0])
        if callback:
            self.selection.Bind(EVT_TEXT, lambda x: callback(self.selection.GetValue()))
        sizer.Add(self.selection)
        self.SetSizer(sizer)

    def get_selection(self):
        return self.selection.GetValue()


class SimpleInput(Panel):

    def __init__(self, parent, label, initial=""):
        super().__init__(parent)

        sizer = BoxSizer(HORIZONTAL)
        self._text_input = TextCtrl(self)
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input)
        sizer.Add(StaticText(self, label=label))
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()


class MyForm(Frame):
    _files = []
    _path = None
    _start = None
    _end = None
    _ffmpeg_path = get_absolute_path('lib\\ffmpeg\\bin\\ffmpeg.exe')

    def __init__(self):

        if not exists(self._ffmpeg_path):
            print('ffmpeg not found')
            raise FileNotFoundError

        Frame.__init__(self, None, ID_ANY, "CUT", size=(300, 500))
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        loc = Icon()
        loc.CopyFromBitmap(Bitmap('icon.ico', BITMAP_TYPE_ANY))
        self.SetIcon(loc)
        panel = Panel(self, EXPAND)
        sizer = BoxSizer(VERTICAL)

        font = Font(30, DECORATIVE, ITALIC, NORMAL) # TODO change font
        self.SetFont(font)

        sizer.Add(FileInput(panel, text="Open File", callback=self._set_target,
                            file_type="*.mkv;*.mp4;*.webm;*.bmp;*.gif;*.png",
                            text_open_file_title="OPEN", text_open_file="File"), 1, EXPAND)

        #  Create Input fields
        self._start_input = SimpleInput(panel, label='START', initial='00:00:00.0')
        self._start_input.SetFont(font)
        self._end_input = SimpleInput(panel, label='END', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='33')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='24')
        # Create check inputs
        self._check_webm = CheckBox(panel, label="WEBM")
        self._check_mp4 = CheckBox(panel, label="MP4")
        self._check_frames = CheckBox(panel, label="FRAMES")
        self._check_gif = CheckBox(panel, label="gif")
        self._check_no_audio = CheckBox(panel, label="No audio")

        # Add inputs to sizer
        sizer.Add(self._start_input, 1, EXPAND)
        sizer.Add(self._end_input, 1, EXPAND)
        sizer.Add(self._scale_input, 1, EXPAND)
        sizer.Add(self._webm_input, 1, EXPAND)
        sizer.Add(self._framerate_input, 1, EXPAND)

        sizer.Add(self._check_webm, 0, EXPAND)
        sizer.Add(self._check_mp4, 0, EXPAND)
        sizer.Add(self._check_frames, 0, EXPAND)
        sizer.Add(self._check_gif, 0, EXPAND)
        sizer.Add(self._check_no_audio, 0, EXPAND)

        # Add Button, and put everything to the panel
        sizer.Add(StandardButton(panel, text='CUT', callback=self._cut), 1, EXPAND)
        panel.SetSizer(sizer)

    def _set_target(self, path, files):
        self._path = path
        self._files = files

    def _run_command(self, file, command, new_file, time):
        if exists(new_file):
            print('ALREADY EXISTS: ', new_file)
            return

        if self._check_no_audio.GetValue():
            no_audio = ' -an'
        else:
            no_audio = ''

        command = ['"' + self._ffmpeg_path + '"',
                   '-i', '"' + file + '"',
                   time, no_audio, command,
                   '"' + new_file + '"']
        command = ' '.join(command)
        print(command)
        Popen(command).communicate()

    def move_files(self, temp_path, files, reverse):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)

            if reverse:
                move(get_full_path(temp_path, file_name), get_full_path(self._path, file))
            else:
                move(get_full_path(self._path, file), get_full_path(temp_path, file_name))

    def _cut(self, event):

        types = ('.bmp', '.png')
        frames = list(filter(lambda x: is_file_type(x, types), self._files))
        videos = list(filter(lambda x: not is_file_type(x, types), self._files))
        # Load frames
        if len(frames) > 1:

            with TemporaryDirectory(prefix=self._path + '/') as temp_path:
                self.move_files(temp_path, frames, reverse=False)
                # Convert the frames
                self._convert(i_file=' -framerate ' + self._framerate_input.get_value() + ' -i' +
                                     get_full_path(temp_path, '%3d' + get_file_type(frames[0])),
                              o_file=self._path, time='')
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
                o_file = get_full_path(self._path, '_' + (self._start_input.get_value() + '_' +
                                                          self._end_input.get_value()).replace(":", "-")
                                       + '_' + remove_file_type(i_file))
                # Convert the video
                self._convert(get_full_path(self._path, i_file), o_file, time)
        # no else

    def _convert(self, i_file, o_file, time):

        if self._check_webm.GetValue():
            self.convert_webm(o_file, i_file, time)

        if self._check_mp4.GetValue():
            self.convert_mp4(o_file, i_file, time)

        if self._check_frames.GetValue():
            with Timer('FRAMES'):
                self.convert_frames(o_file, i_file, time)

        if self._check_gif.GetValue():
            with Timer('GIF'):
                self.convert_gif(o_file, i_file, time)

        print('\nDONE')

    def convert_webm(self, o_file, i_file, time):
        o_file += ".webm"

        command = ' -lavfi "scale=' + self._scale_input.get_value() + '" -c:v libvpx-vp9 -speed 0 -crf ' + self._webm_input.get_value() + \
                  ' -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 ' \
                  '-auto-alt-ref 1 -lag-in-frames 25 -c:a libopus -vbr on -b:a 128k -ac 6'

        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file,
                          time=time)

    def convert_mp4(self, o_file, i_file, time):
        o_file += ".mp4"

        self._run_command(file=i_file,
                          command='-async 1',
                          new_file=o_file,
                          time=time)

    def convert_gif(self, o_file, i_file, time):

        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer():
                palette = palette_dir + '/palette.png'
                self._run_command(file=i_file,
                                  command=' -vf "scale=' + self._scale_input.get_value() + ':flags=lanczos,palettegen"',
                                  new_file=palette,
                                  time=time)
            if not exists(palette):
                print('No Palette')
                return

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"',
                              new_file=o_file + "_bayer.gif",
                              time=time)

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=none"',
                              new_file=o_file + "_none.gif",
                              time=time)

            self._run_command(file=i_file,
                              command=' -lavfi "scale=' + self._scale_input.get_value() + '"',
                              new_file=o_file + '_no_pal.gif',
                              time=time)

    def convert_frames(self, o_file, i_file, time):
        # o_file is output directory for frames
        if exists(o_file):
            print('Exists')
            return
        make_directory(o_file)
        o_file = get_clean_path(get_full_path(o_file, "/%03d.bmp"))
        self._run_command(file=i_file,
                          command='',
                          new_file=o_file,
                          time=time)


if __name__ == "__main__":
    with Logger(debug=True):
        app = App(False)
        frame = MyForm()
        frame.Show()
        app.MainLoop()
