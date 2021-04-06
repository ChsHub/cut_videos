import io
import locale
from datetime import datetime as date
from logging import info
from os import mkdir, startfile
from os.path import join, splitext, split, exists
from re import findall, error
from shutil import copy
from subprocess import Popen, PIPE, STDOUT, getoutput
from tempfile import TemporaryDirectory
from threading import Thread

from timerpy import Timer

from cut_videos.paths import ffmpeg_path, ffprobe_path


def _format_time(time):
    time, milli = splitext(time)
    time = findall(r'([1-9]\d?)|00', time)
    time = '-'.join(time)
    time = time.lstrip('-')
    milli = milli.rstrip('0')
    milli = milli.rstrip('.')
    return time + milli


class Task(Thread):
    def __init__(self, gui, start_time):
        Thread.__init__(self, daemon=True)  # Run in new thread
        self._gui = gui
        self._start_time = start_time
        self._end_time = self._gui._end_input.get_value()

    def get_output_name(self, i_file):
        i_file, _ = splitext(i_file)  # Remove ext
        start_t = _format_time(self._start_time)
        end_t = _format_time(self._gui._end_input.get_value())
        return '_%s_[%s_%s]' % (i_file, start_t, end_t)

    def _convert_frames(self, frames):
        if len(frames) > 1:
            with TemporaryDirectory() as temp_path:
                self.move_files(temp_path, frames)
                # Convert the frames
                self._convert(join(temp_path, '%3d' + splitext(frames[0])[-1]), frames[0], len(frames))

    def run(self):
        types = ('.bmp', '.png', '.jpg', '.webp')
        frames = list(filter(lambda x: splitext(x)[-1].lower() in types, self._gui._files))
        videos = list(filter(lambda x: splitext(x)[-1].lower() not in types, self._gui._files))
        # Load frames
        self._convert_frames(frames)

        # Load videos
        for i_file in videos:
            o_file = self.get_output_name(i_file)
            i_file = join(self._gui._path, i_file)
            # Convert the video
            self._convert(i_file, o_file,
                          self._get_duration(i_file) * self._get_video_fps(i_file))

    def _set_current_frames(self, value):
        frame_nr = int(value)
        self._gui._progress_bar.SetValue(frame_nr)
        self._gui._progress_bar.Update()

    def _set_total_frames(self, total_frames):
        self._gui._progress_bar.SetValue(0)
        self._gui._progress_bar.SetRange(int(total_frames))

    def _get_time(self):
        time = ''
        start_time = self._start_time
        end_time = self._gui._end_input.get_value()
        if start_time != '00:00:00.0' or end_time != '00:00:00.0':
            time = '-sn -ss ' + start_time
        # Cut till end if no input is given
        if end_time != '00:00:00.0':
            time += ' -to ' + end_time
        return time

    def _get_audio_command(self, file):
        # TODO downmix
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        audio_selection = self._gui._audio_select.get_selection()
        audio_codec = self._get_audio_codec(file)

        info('SELECTED: ' + audio_selection)
        info('INPUT: ' + audio_codec)

        # DON'T convert if selected codec is input codec
        audio_command = 'Native format' if audio_codec == audio_selection else audio_selection
        audio_command = self._gui._audio_options[audio_command]
        return audio_command

    def _run_command(self, file, command, new_file):
        input_framerate = self._gui._framerate_input.get_value()
        input_framerate = ' -r ' + input_framerate if input_framerate else ''

        new_file = join(self._gui._path, new_file)
        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Insert selected values into command
        command = command.replace('%scale', self._gui._scale_input.get_value())
        command = command.replace('%crf', self._gui._webm_input.get_value())

        # Output directory for frames
        if not command:
            directory, _ = split(new_file)
            if exists(directory):
                info('Exists')
                return
            mkdir(directory)

        # Resolve selected audio codec
        audio_command = self._get_audio_command(file)

        command = ['"%s"' % ffmpeg_path,
                   input_framerate,
                   '-i "%s"' % file,
                   self._get_time(), audio_command, command,
                   '"%s"' % new_file]
        command = ' '.join(command)
        info(command)

        # Start process
        with Timer('CONVERT'):
            process = Popen(command, shell=False, stdout=PIPE, stderr=STDOUT)
            self._monitor_process(process)
        startfile(split(file)[0])  # Open directory

    def _monitor_process(self, process):
        reader = io.TextIOWrapper(process.stdout, encoding='UTF-8', newline='\r')
        while line := reader.readline():
            if data := findall(r'frame=\s*(\d+)\s+', line):
                info(line)
                self._set_current_frames(data[0])

        result = process.communicate()
        print(result)

    def move_files(self, temp_path, files):
        digits = 3
        for i, file in enumerate(sorted(files)):
            i += 1
            file_name = (digits - len(str(i))) * "0" + str(i) + splitext(file)[-1]
            copy(join(self._gui._path, file), join(temp_path, file_name))

    def _get_audio_codec(self, file):
        command = ffprobe_path + ' -v error -select_streams a:0 -show_entries stream=codec_name \
                        -of default=noprint_wrappers=1:nokey=1 "%s"' % file
        return getoutput(command)

    def _get_video_fps(self, file):
        command = '"%s" -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "%s"'
        command %= (ffprobe_path, file)
        output = getoutput(command)
        if not output:
            return 1  # in case of audio

        output = output.strip()
        if '/' in output:
            output = output.split('/')
            if len(output) == 2:
                return float(output[0]) / float(output[1])
            else:
                raise NotImplementedError

        error('UNKNOWN FRAMERATE VALUE %s' % output)
        raise NotImplementedError
        # return float(24)

    def _get_duration(self, file):
        """
        Get video duration in seconds
        :param file: Video file
        :return: Duration in seconds
        """
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        time_format = '%H:%M:%S.%f'

        if self._end_time == '00:00:00.0':
            command = '"%s" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -sexagesimal "%s"'
            command %= (ffprobe_path, file)
            self._end_time = getoutput(command)

        result = date.strptime(self._end_time, time_format) - date.strptime(self._start_time, time_format)
        return result.total_seconds()

    def _convert(self, i_file, o_file, frame_count):
        self._set_total_frames(frame_count)
        info('CONVERT %s to %s' % (i_file, o_file))
        command, suffix = self._gui._video_options[self._gui._video_select.get_selection()]
        suffix = suffix.replace('%ext', splitext(i_file)[-1])  # COPY keep same ext
        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file + suffix)

    info('DONE')
