from datetime import datetime as date
from logging import info
from re import findall
from shutil import move
from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory
from threading import Thread

from os.path import join
from timerpy import Timer
from utility.os_interface import exists, make_directory
from utility.path_str import get_clean_path
from utility.utilities import get_file_type, remove_file_type, is_file_type


class Task(Thread):
    _frame_format = '.png'

    def __init__(self, gui):
        Thread.__init__(self, daemon=True)
        self._gui = gui

        # Get the length of the new video in seconds
        FMT = '%H:%M:%S.%f'
        self.total_frames = date.strptime(self._gui._end_input.get_value(), FMT) - date.strptime(
            self._gui._start_input.get_value(), FMT)
        self.total_frames = self.total_frames.total_seconds()

    def run(self):
        types = ('.bmp', '.png', '.jpg')
        frames = list(filter(lambda x: is_file_type(x, types), self._gui._files))
        videos = list(filter(lambda x: not is_file_type(x, types), self._gui._files))
        # Load frames
        if len(frames) > 1:
            with TemporaryDirectory(prefix=self._gui._path + '/') as temp_path:
                self._gui.move_files(temp_path, frames, reverse=False)
                # Convert the frames
                input_framerate = ' -framerate ' + self._gui._framerate_input.get_value()
                self._gui._convert(i_file=join(temp_path, '%3d' + get_file_type(frames[0])),
                                   o_file=self._gui._path, time='', input_framerate=input_framerate)
                self._gui.move_files(temp_path, frames, reverse=True)
        # no else

        # Load videos
        if len(videos) >= 1:
            # Get time settings
            if self._gui._end_input.get_value() == '00:00:00.0':
                time = ''
            else:
                time = '-sn -ss ' + self._gui._start_input.get_value() + ' -to ' + self._gui._end_input.get_value()

            for i_file in videos:
                # Get output file name
                o_file = join(self._gui._path, '_' + (self._gui._start_input.get_value() + '_' +
                                                      self._gui._end_input.get_value()).replace(":", "-")
                              + '_' + remove_file_type(i_file))
                # Convert the video
                self._convert(join(self._gui._path, i_file), o_file, time)
        # no else

    def _set_current_frames(self, value):
        frame_nr = int(value)
        self._gui._progress_bar.SetValue(frame_nr)

    def _set_total_frames(self, value):
        self.total_frames *= float(value)
        self._gui._progress_bar.SetRange(int(self.total_frames))

    def _run_command(self, file, command, new_file, time, input_framerate=''):

        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Resolve selected audio codec
        audio = self._gui._audio_options[self._gui._audio_select.get_selection()]

        command = ['"' + self._gui._ffmpeg_path + '"',
                   input_framerate, '-i', '"' + file + '"',
                   time, audio, command,
                   '"' + new_file + '"']
        command = ' '.join(command)
        info(command)

        info('CONVERT')
        process = Popen(command, stderr=PIPE)

        # READ OUTPUT
        symbol = ' '
        line = b''

        pattern = '\s(\d+\S+)\sfps'  # FPS pattern
        strategy = self._set_total_frames

        while symbol:
            symbol = process.stderr.read(90)
            line += symbol

            data = findall(pattern, str(line))
            if data:
                line = b''
                strategy(data[0])

                # If FPS found, search frame numbers
                pattern = 'frame=\s*(\d+)\s+'
                strategy = self._set_current_frames
                self._gui._progress_bar.Update()

        process.communicate()

    def move_files(self, temp_path, files, reverse):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)

            if reverse:
                move(join(temp_path, file_name), join(self._gui._path, file))
            else:
                move(join(self._gui._path, file), join(temp_path, file_name))

    def _convert(self, i_file, o_file, time, input_framerate=''):

        if self._gui._check_webm.GetValue():
            self.convert_webm(o_file, i_file, time, input_framerate=input_framerate)

        if self._gui._check_mp4.GetValue():
            self.convert_mp4(o_file, i_file, time, input_framerate=input_framerate)

        if self._gui._check_frames.GetValue():
            with Timer('FRAMES', log_function=info):
                self.convert_frames(o_file, i_file, time, input_framerate=input_framerate)

        if self._gui._check_gif.GetValue():
            with Timer('GIF', log_function=info):
                self.convert_gif(o_file, i_file, time, input_framerate=input_framerate)

        info('\nDONE')

    def convert_webm(self, o_file, i_file, time, input_framerate=''):
        o_file += ".webm"
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        command = ' -lavfi "scale=' + self._gui._scale_input.get_value() + '" -c:v libvpx-vp9 -speed 0 -crf ' + self._gui._webm_input.get_value() + \
                  ' -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 ' \
                  '-auto-alt-ref 1 -lag-in-frames 25'

        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file,
                          time=time, input_framerate=input_framerate)

    def convert_mp4(self, o_file, i_file, time, input_framerate=''):
        o_file += ".mp4"

        self._run_command(file=i_file,
                          command='-async 1 -lavfi "scale=' + self._gui._scale_input.get_value() + '"',
                          new_file=o_file,
                          time=time, input_framerate=input_framerate)

    def convert_gif(self, o_file, i_file, time, input_framerate=''):

        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer('GENERATE PALETTE', log_function=info):
                palette = palette_dir + '/palette.png'
                self._run_command(file=i_file,
                                  command=' -vf "scale=' + self._gui._scale_input.get_value() + ':flags=lanczos,palettegen"',
                                  new_file=palette,
                                  time=time, input_framerate=input_framerate)
            if not exists(palette):
                info('No Palette')
                return

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._gui._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"',
                              new_file=o_file + "_bayer.gif",
                              time=time, input_framerate=input_framerate)

            self._run_command(file=i_file + '" -i "' + palette,
                              command=' -lavfi "scale=' + self._gui._scale_input.get_value() + ':flags=lanczos,paletteuse=dither=none"',
                              new_file=o_file + "_none.gif",
                              time=time, input_framerate=input_framerate)

            self._run_command(file=i_file,
                              command=' -lavfi "scale=' + self._gui._scale_input.get_value() + '"',
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
