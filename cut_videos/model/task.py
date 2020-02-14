from datetime import datetime as date
from logging import info
from re import findall
from shutil import move
from subprocess import Popen, PIPE, STDOUT
from tempfile import TemporaryDirectory
from threading import Thread

from os.path import join, splitext, split, abspath
from timerpy import Timer
from utility.os_interface import exists, make_directory
from utility.path_str import get_clean_path
from utility.utilities import get_file_type, remove_file_type, is_file_type


class Task(Thread):

    def __init__(self, gui, path, files):
        Thread.__init__(self, daemon=True)

        self._gui = gui
        self._path = path
        self._files = files
        self._time_start = None
        self._time_end = None
        self._total_frames = None
        self._ffmpeg_path = abspath('lib\\ffmpeg\\bin\\ffmpeg.exe')

        if not exists(self._ffmpeg_path):
            info('ffmpeg not found')
            raise FileNotFoundError

    def set_time(self, start, end):
        self._time_end = end
        self._time_start = start

        # Get the length of the new video in seconds
        FMT = '%H:%M:%S.%f'
        self._total_frames = date.strptime(start, FMT) - date.strptime(end, FMT)
        self._total_frames = self._total_frames.total_seconds()

    def run(self):
        types = ('.bmp', '.png', '.jpg')
        frames = list(filter(lambda x: is_file_type(x, types), self._files))
        videos = list(filter(lambda x: not is_file_type(x, types), self._files))
        # Load frames
        if len(frames) > 1:
            with TemporaryDirectory(prefix=self._path + '/') as temp_path:
                self.move_files(temp_path, frames, reverse=False)

                # Convert the frames
                input_framerate = ' -framerate ' + self._gui._framerate_input.get_value()
                self._convert(i_file=join(temp_path, '%3d' + get_file_type(frames[0])),
                              o_file=self._path, input_framerate=input_framerate)
                self.move_files(temp_path, frames, reverse=True)
        # no else

        # Load videos
        if len(videos) >= 1:
            for i_file in videos:
                # Get output file name
                o_file = join(self._path, '_' + (self._time_start + '_' +
                                                 self._time_end).replace(":", "-")
                              + '_' + remove_file_type(i_file))
                # Convert the video
                self._convert(join(self._path, i_file), o_file)
        # no else

    def _set_current_frames(self, value):
        frame_nr = int(value)
        self._gui._progress_bar.SetValue(frame_nr)

    def _set_total_frames(self, value):
        self._total_frames *= float(value)
        self._gui._progress_bar.SetValue(0)
        self._gui._progress_bar.SetRange(int(self._total_frames))

    def _run_command(self, file, command, new_file, input_framerate=''):
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Get time settings
        time = ''
        if self._time_end != '00:00:00.0':
            time = '-sn -ss ' + self._time_start + ' -to ' + self._time_end

        # Insert selected values into command
        command = command.replace('%scale', self._gui._scale_input.get_value())
        command = command.replace('%crf', self._gui._webm_input.get_value())
        _, ext = splitext(file)
        new_file = new_file.replace('%ext', ext)

        # Output directory for frames
        if not command:
            directory, _ = split(new_file)
            if exists(directory):
                info('Exists')
                return
            make_directory(directory)

        # Resolve selected audio codec
        audio = self._gui._audio_options[self._gui._audio_select.get_selection()]

        command = ['"' + self._gui._ffmpeg_path + '"',
                   input_framerate, '-i', '"' + file + '"',
                   time, audio, command,
                   '"' + get_clean_path(new_file) + '"']
        command = ' '.join(command)
        info(command)

        # CONVERT
        with Timer('CONVERT'):
            process = Popen(command, shell=False, stdout=PIPE, stderr=STDOUT)

            # READ OUTPUT
            symbol = ' '
            line = b''
            pattern = '\s(\d+\S+)\sfps'  # FPS pattern
            strategy = self._set_total_frames

            while symbol:
                symbol = process.stdout.read(92)
                line += symbol

                data = findall(pattern, str(line))
                if data:
                    info(str(line))
                    line = b''
                    strategy(data[0])

                    # If FPS found, search frame numbers
                    pattern = 'frame=\s*(\d+)\s+'  # Frame pattern
                    strategy = self._set_current_frames
                    self._gui._progress_bar.Update()

            process.communicate()

    def move_files(self, temp_path, files, reverse):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)

            if reverse:
                move(join(temp_path, file_name), join(self._path, file))
            else:
                move(join(self._path, file), join(temp_path, file_name))

    def _convert(self, i_file, o_file, input_framerate=''):

        if self._gui._video_select.get_selection() == 'gif':
            self.convert_gif(o_file, i_file, input_framerate=input_framerate)
        else:
            command, suffix = self._gui._video_options[self._gui._video_select.get_selection()]
            self._run_command(file=i_file,
                              command=command,
                              new_file=o_file + suffix,
                              input_framerate=input_framerate)

        info('\nDONE')

    def convert_gif(self, o_file, i_file, input_framerate=''):

        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer('GENERATE PALETTE', log_function=info):
                palette = palette_dir + '/palette.png'
                self._run_command(file=i_file,
                                  command=' -vf "scale=' + self._gui._scale_input.get_value() + ':flags=lanczos,palettegen"',
                                  new_file=palette,
                                  input_framerate=input_framerate)
            if not exists(palette):
                info('No Palette')
                return

            for mode, suffix in [
                (':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle', "_bayer.gif"),
                (':flags=lanczos,paletteuse=dither=none', "_default.gif"),
                ('', '_no_pal.gif')]:
                self._run_command(file=i_file + '" -i "' + palette,
                                  command=' -lavfi "scale=%s%s"' % (self._gui._scale_input.get_value(), mode),
                                  new_file=o_file + suffix,
                                  input_framerate=input_framerate)
