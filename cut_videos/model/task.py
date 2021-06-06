import io
import locale
from datetime import datetime
strptime = datetime.strptime
from logging import info
from os import mkdir, startfile
from os.path import join, splitext, split, exists
from re import findall, error
from subprocess import Popen, PIPE, STDOUT, getoutput
from tempfile import TemporaryDirectory
from threading import Thread

from PIL import Image
from timerpy import Timer

from cut_videos.commands import audio_options, image_types, digits, input_ext, duration_command, fps_command
from cut_videos.paths import ffmpeg_path, ffprobe_path

time_format = '%H:%M:%S.%f'


def _format_time(time):
    time, milli = splitext(time)
    time = findall(r'([1-9]\d?)|00', time)
    time = '-'.join(time)
    time = time.lstrip('-')
    milli = milli.rstrip('0')
    milli = milli.rstrip('.')
    return time + milli


class Task(Thread):

    def __init__(self, window):
        Thread.__init__(self, daemon=True)  # Run in new thread
        self._start_time = window.start_time
        self._end_time = window.end_time
        self._path = window.path
        self._files = window.files.copy()
        self._video_selection = window.video_selection
        self._audio_selection = window.audio_selection
        self._set_total_frames = window.set_total_frames
        self._set_current_frame_nr = window.set_current_frame_nr
        self._scale_input = window.scale_input
        self._webm_input = window.webm_input
        self._duration = None
        start_s, start_ms = self._start_time.split('.')
        self.static_command = ['"%s"' % ffmpeg_path,
                               '-sn',  # '-sn' Automatic stream selection
                               ' -r ' + window.input_framerate if window.input_framerate else '',
                               '-ss ' + start_s,  # Seeking on input file is faster https://trac.ffmpeg.org/wiki/Seeking
                               '-i "%s"',
                               '-ss 0.' + start_ms,
                               '-to ' + str(strptime(window.end_time, time_format)
                                            - strptime(start_s + '.0', time_format))
                               if self._end_time != '00:00:00.0' else ''  # Cut to end if no input is given
                               ]
        self.static_command = ' '.join(self.static_command)

    def get_output_name(self, i_file):
        i_file, _ = splitext(i_file)  # Remove ext
        start_t = _format_time(self._start_time)
        end_t = _format_time(self._end_time)
        return '_%s_[%s_%s]' % (i_file, start_t, end_t)

    def _convert_frames(self, frames):
        if len(frames) > 1:
            with TemporaryDirectory() as temp_path:
                self.copy_files(temp_path, frames, input_ext)
                # Convert the frames
                self._set_total_frames(len(frames))
                self._convert(join(temp_path, '%%%sd' % digits + input_ext), frames[0])

    def _convert_videos(self, videos):
        # Load videos
        for i_file in videos:
            o_file = self.get_output_name(i_file)
            i_file = join(self._path, i_file)
            # Convert the video
            self._set_total_frames(self._get_duration(i_file) * self._get_video_fps(i_file))
            self._convert(i_file, o_file)

    def run(self):
        frames = list(filter(lambda x: splitext(x)[-1].lower() in image_types, self._files))
        videos = list(filter(lambda x: splitext(x)[-1].lower() not in image_types, self._files))
        # Load frames
        self._convert_frames(frames)
        self._convert_videos(videos)

        startfile(self._path)  # Open directory when finished

    def _get_audio_command(self, file):
        # TODO downmix
        # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg
        audio_codec = self._get_audio_codec(file)

        info('SELECTED: ' + self._audio_selection)
        info('INPUT: ' + audio_codec)

        # DON'T convert if selected codec is input codec
        audio_command = 'Native format' if audio_codec == self._audio_selection else self._audio_selection
        return audio_options[audio_command]

    def _run_command(self, file, command, new_file):

        new_file = join(self._path, new_file)
        if exists(new_file):
            info('ALREADY EXISTS: ' + new_file)
            return

        # Insert selected values into command
        command = command.replace('<res>', self._scale_input)
        command = command.replace('<crf>', self._webm_input)

        # Output directory for frames
        if not command:
            directory, _ = split(new_file)
            if exists(directory):
                info('Exists')
                return
            mkdir(directory)

        command = [self.static_command % file,
                   self._get_audio_command(file),
                   command,
                   '"%s"' % new_file]
        command = ' '.join(command)
        info(command)

        # Start process
        with Timer('CONVERT'):
            process = Popen(command, shell=False, stdout=PIPE, stderr=STDOUT)
            self._monitor_process(process)

    def _monitor_process(self, process):
        reader = io.TextIOWrapper(process.stdout, encoding='UTF-8', newline='\r')
        while line := reader.readline():
            if data := findall(r'frame=\s*(\d+)\s+', line):
                info(line)
                self._set_current_frame_nr(data[0])

        result = process.communicate()
        print(result)

    def copy_files(self, temp_path, files, ext):
        for i, file in enumerate(sorted(files)):
            file_name = digits * "0" + str(i + 1)
            with Image.open(join(self._path, file)) as image:
                image.save(join(temp_path, file_name[-digits:] + ext), quality=100)

    def _get_audio_codec(self, file):
        command = ffprobe_path + ' -v error -select_streams a:0 -show_entries stream=codec_name \
                        -of default=noprint_wrappers=1:nokey=1 "%s"' % file
        return getoutput(command)

    def _get_video_fps(self, file):
        output = getoutput(fps_command % (ffprobe_path, file))
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
        result = self._end_time

        if result == '00:00:00.0':  # Run probe to find video length
            result = getoutput(duration_command % (ffprobe_path, file))

        result = strptime(result, time_format) - strptime(self._start_time, time_format)
        return result.total_seconds()

    def _convert(self, i_file, o_file):
        info('CONVERT %s to %s' % (i_file, o_file))
        command, suffix = self._video_selection
        suffix = suffix.replace('%ext', splitext(i_file)[-1])  # COPY keep same ext
        self._run_command(file=i_file,
                          command=command,
                          new_file=o_file + suffix)
        info('DONE')
