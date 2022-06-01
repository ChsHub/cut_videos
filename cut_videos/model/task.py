import io
import locale
from datetime import datetime
from logging import info, exception
from os import startfile
from os.path import splitext
from pathlib import Path
from re import findall, error
from subprocess import Popen, PIPE, STDOUT, getoutput
from tempfile import TemporaryDirectory
from threading import Thread

from PIL import Image
from timerpy import Timer

from cut_videos.resources.commands import audio_options, image_types, digits, frame_input_ext, duration_command, \
    fps_command, audio_codec_command, original_audio, video_options
from cut_videos.resources.gui_texts import frames_text
from cut_videos.resources.paths import ffmpeg_path

strptime = datetime.strptime
time_format = '%H:%M:%S.%f'
zero_time = '00:00:00.000'


def unformat_time(time: str) -> str:
    """
    Convert stort time string to long form (digits only)
    :param time: Short time string
    :return: Long format time 8 digit string
    """
    if '.' in time:
        time, milli = time.split('.')
        milli += (2 - len(milli)) * '0'  # Add trailing zeroes
    else:
        milli = '00'

    # Add redundant zeroes
    time = time.split('-')
    while len(time) < 3:
        time = ['00'] + time
    for i, t in enumerate(time):
        time[i] = (2 - len(t)) * '0' + t

    return ''.join(time) + milli


def _format_time(time: str) -> str:
    """
    Format time to shortened human readable form
    :param time: Time string in long form
    :return: Time string in shortened form
    """
    time, milli = splitext(time)
    time = findall(r'([1-9]\d?)|00', time)
    time = '-'.join(time)
    time = time.lstrip('-')
    milli = milli.rstrip('0')
    milli = milli.rstrip('.')
    return time + milli


class Task(Thread):
    """
    Run convesion command in thread executor
    """

    def __init__(self,
                 input_framerate,
                 start_time,
                 end_time,
                 hardsub,
                 webm_input,
                 scale_input,
                 audio_selection,
                 video_selection,
                 path,
                 files,
                 bar):
        Thread.__init__(self, daemon=True)
        self._set_total_frames = bar.set_total_frames
        self._set_current_frame_nr = bar.set_current_frame_nr
        self.input_framerate = input_framerate
        self.start_time = start_time
        self.end_time = end_time
        self.hardsub = hardsub
        self.webm_input = webm_input
        self.scale_input = scale_input
        self.audio_selection = audio_selection
        self.video_selection = video_selection
        self.path = path
        self.files = files

        self.start()

    def run(self):
        """
        Run thread and start conversion
        :return:
        """
        # Load frames
        self._convert_frames()
        self._convert_videos()

        # Set bar to full
        self._set_total_frames(10)
        self._set_current_frame_nr(11)
        # Open directory when finished
        startfile(self.path)

    def _convert_frames(self):
        """
        Convert frames to video
        """
        frames = [x for x in self.files if Path(x).suffix in image_types]
        if len(frames) > 1:
            with TemporaryDirectory() as temp_path:
                self._copy_files(temp_path, frames, frame_input_ext)
                self._set_total_frames(len(frames))
                self._run_command(Path(temp_path, '%%%sd' % digits + frame_input_ext), frames[0])

    def _convert_videos(self):
        """
        Convert videos
        """
        # Load videos
        for file_input in [x for x in self.files if Path(x).suffix not in image_types]:
            file_input = Path(self.path, file_input)
            # Convert the video
            self._set_total_frames(self._get_duration(file_input) * self._get_video_fps(file_input))
            self._run_command(file_input,
                              f'_{file_input.stem}_[{_format_time(self.start_time)}_{_format_time(self.end_time)}]')

    # TODO downmix
    # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg

    def _run_command(self, file_input: Path, file_output: str):
        """
        Check file paths, and run the command with file_input and file_output
        :param file_input: Input file
        :param command: Conversion command
        :param file_output: Output file
        """

        # Check new file_input
        command, suffix = video_options[self.video_selection]
        suffix = suffix.replace('%ext', file_input.suffix)  # COPY keep same ext
        file_output += suffix
        info(f'CONVERT {file_input} to {file_output}')

        file_output = Path(self.path, file_output)
        directory = file_output.parent  # Output directory for frames
        if file_output.exists() or ((self.video_selection == frames_text) and directory.exists()):
            info(f'ALREADY EXISTS: {file_output}')
            return
        directory.mkdir(exist_ok=True)

        start_s, start_ms = self.start_time.split('.')
        command = [ffmpeg_path,
                   '-sn',  # '-sn' Automatic stream selection
                   ' -r ' + self.input_framerate if self.input_framerate else '',
                   '-ss ' + start_s if self.start_time != zero_time else '',
                   # Seeking on input file_input is faster https://trac.ffmpeg.org/wiki/Seeking
                   f'-i "{file_input}"',
                   '-ss 0.' + start_ms if self.start_time != zero_time else '',
                   '-to ' + str(strptime(self.end_time, time_format) - strptime(start_s + '.0', time_format))
                   if self.end_time != zero_time else '',  # Cut to end if no input is given
                   f'-vf subtitles="{file_input}"' if self.hardsub else '',
                   audio_options[
                       original_audio if getoutput(
                           audio_codec_command % file_input) == self.audio_selection else self.audio_selection],
                   # Don't convert audio if selected is same as input
                   command.replace('<crf>', self.webm_input).replace('<res>', self.scale_input)
                   ]
        info(' '.join(command))

        # Start process
        with Timer('CONVERT'):
            process = Popen(command, shell=False, stdout=PIPE, stderr=STDOUT)
            self._monitor_process(process)

    def _monitor_process(self, process):
        """
        Read ffmpeg output
        :param process: process object
        """
        reader = io.TextIOWrapper(process.stdout, encoding='UTF-8', newline='\r')
        while line := reader.readline():
            if data := findall(r'frame=\s*(\d+)\s+', line):
                self._set_current_frame_nr(data[0])

        result = process.communicate()
        print(result)

    def _copy_files(self, temp_path: str, files: list, ext):
        """
        Copy files to temporary directory
        :param temp_path:
        :param path:
        :param files:
        :param ext:
        :return:
        """
        for i, file in enumerate(sorted(files)):  # , key=lambda x: int(splitext(x)[0])
            file_name = digits * '0' + str(i + 1)
            with Image.open(Path(self.path, file)) as image:
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(Path(temp_path, file_name[-digits:] + ext), quality=100)

    def _get_video_fps(self, file):
        output = getoutput(fps_command % file)
        if not output:
            return 1  # in case of audio

        output = output.strip()
        if '/' in output:
            output = output.split('/')
            if len(output) == 2:
                return float(output[0]) / float(output[1])
            elif len(output) == 3:
                return float(output[0]) / float(output[1].split('\n')[0])
            else:
                exception(f'GET FPS FAIL {output}')

        error(f'UNKNOWN FRAMERATE VALUE {output}')
        raise NotImplementedError

    def _get_duration(self, file):
        """
        Get video duration in seconds
        :param file: Video file_input
        :return: Duration in seconds
        """
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        result = strptime(self.end_time if self.end_time != zero_time else getoutput(duration_command % file),
                          time_format) - \
                 strptime(self.start_time, time_format)
        return result.total_seconds()
