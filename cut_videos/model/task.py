from datetime import datetime as date
from logging import info
from os import mkdir
from os.path import join, splitext, split, exists
from re import findall
from shutil import copy
from subprocess import Popen, PIPE, STDOUT, getoutput
from tempfile import TemporaryDirectory
from threading import Thread

from timerpy import Timer
from utility.path_str import get_clean_path
from utility.utilities import get_file_type, is_file_type


class Task(Thread):

    def __init__(self, gui):
        Thread.__init__(self, daemon=True)
        self._gui = gui

    def run(self):
        types = ('.bmp', '.png', '.jpg')
        frames = list(filter(lambda x: is_file_type(x, types), self._gui._files))
        videos = list(filter(lambda x: not is_file_type(x, types), self._gui._files))
        input_framerate = self._gui._framerate_input.get_value()
        # Load frames
        if len(frames) > 1:
            if input_framerate:
                input_framerate = ' -framerate ' + input_framerate

            with TemporaryDirectory() as temp_path:
                self.move_files(temp_path, frames)
                # Convert the frames
                self._set_total_frames(len(frames))
                self._convert(i_file=join(temp_path, '%3d' + get_file_type(frames[0])),
                              o_file=self._gui._path, input_framerate=(1, input_framerate))
        # no else

        # Load videos
        if len(videos):
            if input_framerate:
                input_framerate = ' -r ' + input_framerate

            for i_file in videos:
                o_file = join(self._gui._path, '_' + (self._gui._start_input.get_value() + '_' +
                                                      self._gui._end_input.get_value()).replace(":", "-")
                              + '_' + i_file)
                o_file, _ = splitext(o_file)
                i_file = join(self._gui._path, i_file)
                # Convert the video
                self._set_total_frames(self._get_duration(i_file) * self._get_video_fps(i_file))
                self._convert(i_file, o_file, input_framerate=(1, input_framerate))
        # no else

    def _set_current_frames(self, value):
        frame_nr = int(value)
        self._gui._progress_bar.SetValue(frame_nr)
        self._gui._progress_bar.Update()

    def _set_total_frames(self, total_frames):
        self._gui._progress_bar.SetValue(0)
        self._gui._progress_bar.SetRange(int(total_frames))

    def _get_time(self):
        time = ''
        if self._gui._start_input.get_value() != '00:00:00.0':
            time = '-sn -ss ' + self._gui._start_input.get_value()
            # Cut till end if no input is given
            if self._gui._end_input.get_value() != '00:00:00.0':
                time += ' -to ' + self._gui._end_input.get_value()
        return time

    def _get_audio_command(self, file):
        audio_selection = self._gui._audio_select.get_selection()
        info('SELECTED: ' + audio_selection)
        audio_codec = self._get_audio_codec(file)
        info('INPUT: ' + audio_codec)
        if audio_codec == audio_selection:
            return list(self._gui._audio_options.values())[-1]  # DON'T convert if selected codec is input codec
        return self._gui._audio_options[audio_selection]

    def _run_command(self, file, command, new_file, input_framerate: tuple):
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Get time settings
        time = self._get_time()

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
            mkdir(directory)

        # Resolve selected audio codec
        audio_command = self._get_audio_command(file)

        command = ['"%s"' % self._gui._ffmpeg_path,
                   '-i "%s"' % file,
                   time, audio_command, command,
                   '"%s"' % get_clean_path(new_file)]
        if input_framerate:
            index, input_framerate = input_framerate
            command.insert(index, input_framerate)
        command = ' '.join(command)
        info(command)

        # CONVERT
        with Timer('CONVERT'):
            process = Popen(command, shell=False, stdout=PIPE, stderr=STDOUT)
            self._monitor_process(process)

    def _monitor_process(self, process):
        symbol = ' '
        line = b''
        while symbol:
            symbol = process.stdout.read(92)
            line += symbol

            data = findall('frame=\s*(\d+)\s+', str(line))
            if data:
                info(str(line))
                line = b''
                self._set_current_frames(data[0])

        process.communicate()

    def move_files(self, temp_path, files):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + get_file_type(file)
            copy(join(self._gui._path, file), join(temp_path, file_name))

    def _get_audio_codec(self, file):
        command = self._gui._ffprobe_path + ' -v error -select_streams a:0 -show_entries stream=codec_name \
                        -of default=noprint_wrappers=1:nokey=1 "%s"' % file
        return getoutput(command)

    def _get_video_fps(self, file):
        command = self._gui._ffprobe_path + ' -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 ' \
                                            '-show_entries stream=r_frame_rate "%s"' % file
        fps_n, fps_z = getoutput(command).split('/')
        return float(fps_n) / float(fps_z)

    def _get_duration(self, file):
        """
        Get video duration in seconds
        :param file: Video file
        :return: Duration in seconds
        """
        FMT = '%H:%M:%S.%f'
        result = date.strptime(self._gui._end_input.get_value(), FMT) - date.strptime(
            self._gui._start_input.get_value(), FMT)
        result = result.total_seconds()

        if result == 0.0:
            command = '"%s" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "%s"'
            command %= (self._gui._ffprobe_path, file)
            result = float(getoutput(command))
        return result

    def _convert(self, i_file, o_file, input_framerate: tuple):

        command, suffix = self._gui._video_options[self._gui._video_select.get_selection()]
        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file + suffix,
                          input_framerate=input_framerate)

    info('DONE')
