
from shutil import move
from subprocess import Popen
from tempfile import TemporaryDirectory

from utility.logger import Logger
from utility.os_interface import get_full_path, exists, make_directory, get_absolute_path
from utility.path_str import get_clean_path
from utility.timer import Timer
from utility.utilities import get_file_type, remove_file_type
from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL
from wx import Frame, ID_ANY, App, EXPAND, HORIZONTAL, EVT_CLOSE, CheckBox, Icon, Bitmap, \
    BITMAP_TYPE_ANY
from wx import TextCtrl
from wxwidgets.file_input import FileInput
from wxwidgets.standard_button import StandardButton


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
    _files = None
    _path = None
    _start = None
    _duration = None

    def __init__(self):

        self._ffmpeg_path = get_absolute_path('lib\\ffmpeg\\bin\\ffmpeg.exe')
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

        sizer.Add(FileInput(panel, text="Open File", callback=self._set_target,
                            file_type="*.mkv;*.mp4;*.webm;*.bmp;*.gif",
                            text_open_file_title="OPEN", text_open_file="File"), 1, EXPAND)

        self._start_input = SimpleInput(panel, label='START', initial='00:00:00.0')
        self._duration_input = SimpleInput(panel, label='DURATION', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='33')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='24')

        sizer.Add(self._start_input, 1, EXPAND)
        sizer.Add(self._duration_input, 1, EXPAND)
        sizer.Add(self._scale_input, 1, EXPAND)
        sizer.Add(self._webm_input, 1, EXPAND)
        sizer.Add(self._framerate_input, 1, EXPAND)

        self.check_webm = CheckBox(panel, label="WEBM")
        sizer.Add(self.check_webm, 0, EXPAND)
        self.check_mp4 = CheckBox(panel, label="MP4")
        sizer.Add(self.check_mp4, 0, EXPAND)
        self._check_frames = CheckBox(panel, label="FRAMES")
        sizer.Add(self._check_frames, 0, EXPAND)
        self._check_gif = CheckBox(panel, label="gif")
        sizer.Add(self._check_gif, 0, EXPAND)

        sizer.Add(StandardButton(panel, text='CUT', callback=self._cut), 1, EXPAND)

        panel.SetSizer(sizer)

    def _set_target(self, path, files):
        self._path = path
        self._files = files

    def _set_start(self, start):
        self._start = start

    def _set_duration(self, duration):
        self._duration = duration

    def _run_command(self, file, command, new_file, time):
        if exists(new_file):
            print('Already exists: ', new_file)
            return

        command = self._ffmpeg_path + file + time + command + new_file + '"'
        # with TemporaryDirectory() as temp_dir:
        # write_file_data('.', "a.cmd", command)
        print(command)
        # Popen("a.cmd").communicate()
        Popen(command).communicate()
        # self._executor.submit(Popen, command)

    def _cut(self, event):

        if not self._files:
            return

        # load frames
        if len(self._files) > 1:

            with TemporaryDirectory(prefix=self._path+'/') as temp_path:
                digits = 3
                for i, file in enumerate(sorted(self._files)):
                    i += 1
                    file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)
                    move(get_full_path(self._path, file), get_full_path(temp_path, file_name))

                self._convert(' -framerate ' + self._framerate_input.get_value() + ' -i "' + get_full_path(temp_path, '%3d.bmp'), self._path, '"')

                for i, file in enumerate(sorted(self._files)):
                    i += 1
                    file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)
                    move(get_full_path(temp_path, file_name), get_full_path(self._path, file))
        # load video
        elif len(self._files) == 1:
            if self._start_input.get_value() == '00:00:00.0' and self._duration_input.get_value() == '00:00:00.0':
                time = '"'
            else:
                time = '" -sn -ss ' + self._start_input.get_value() + ' -t ' + self._duration_input.get_value()

            i_file = self._files[0]
            o_file = get_full_path(self._path, '_' + (self._start_input.get_value() + '_' +
                                                      self._duration_input.get_value()).replace(":", "-")
                                   + '_' + remove_file_type(i_file))

            self._convert(' -i "' + get_full_path(self._path, i_file), o_file, time)

    def _convert(self, i_file, o_file, time):

        if self.check_webm.GetValue():
            self.convert_webm(o_file, i_file, time)

        if self.check_mp4.GetValue():
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
        command = ' -lavfi "scale=' + self._scale_input.get_value() + '" -c:v libvpx-vp9 -speed 0 -crf ' + self._webm_input.get_value()+\
                  ' -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 '' \
                  ''-auto-alt-ref 1 -lag-in-frames 25 -c:a libopus -vbr on -b:a 128k -ac 6 "'
        self._run_command(i_file, command, o_file, time)

    def convert_mp4(self, o_file, i_file, time):
        o_file += ".mp4"
        if exists(o_file):
            print('Exists')
            return
        self._run_command(i_file, ' -async 1 "', o_file, time)

    def convert_gif(self, o_file, i_file, time):

        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer():
                palette = palette_dir + '/palette.png'
                self._run_command(i_file, ' -vf "scale=' + self._scale_input.get_value() + ':flags=lanczos,palettegen" "',
                                  palette, time)
            if not exists(palette):
                print('No Palette')
                return

            self._run_command(i_file + '" -i "' + palette,
                                  ' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" "',
                                  o_file + "_bayer.gif", time)

            self._run_command(i_file + '" -i "' + palette,
                                  ' -lavfi "scale=' + self._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=none" "',
                                  o_file + "_none.gif",
                                  time)

            self._run_command(i_file, ' -lavfi "scale=' + self._scale_input.get_value() + '" "',
                                  o_file + '_no_pal.gif', time)

    def convert_frames(self, o_file, i_file, time):
        # o_file is output directory for frames
        if exists(o_file):
            print('Exists')
            return
        make_directory(o_file)
        o_file = get_clean_path(get_full_path(o_file, "%03d.bmp"))
        # command = ' -r 24/1 "'
        command = ' "'
        self._run_command(i_file, command, o_file, time)


if __name__ == "__main__":
    with Logger(debug=True):
        app = App(False)
        frame = MyForm()
        frame.Show()
        app.MainLoop()
