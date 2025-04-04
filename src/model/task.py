import io
import json
import locale
from logging import info, exception
from os import startfile
from pathlib import Path
from re import error
from subprocess import Popen, PIPE, STDOUT, getoutput
from tempfile import TemporaryDirectory
from threading import Thread, Semaphore
from logger_default import Logger
from PIL import Image

from src.model.time_format import *
from src.resources.commands import audio_options, image_types, digits, frame_input_ext, duration_command, \
    fps_command, audio_codec_command, original_audio, video_options
from src.resources.gui_texts import frames_text
from src.resources.paths import ffmpeg_path


class Task(Thread):
    """
    Run conversion command in thread executor
    """

    def __init__(self, input_framerate: str,
                 start_time: str,
                 end_time: str,
                 hardsub: int,
                 webm_input: str,
                 scale_input: str,
                 audio_selection: str,
                 video_selection: str,
                 path: str,
                 files: list,
                 remove_task: callable,
                 bar):

        Thread.__init__(self)
        # GUI
        self._set_total_frames = bar.set_total_frames
        self._set_current_frame_nr = bar.set_current_frame_nr
        self._remove_task = remove_task

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
        self._process = None
        self._current_file = None
        self._closed = False
        self._closed_semaphore = Semaphore(1)
        self.start()

    def run(self):
        """
        Run thread and start conversion
        :return:
        """
        try:
            info('Start Run')
            # Load frames
            self._convert_frames()
            self._convert_videos()

            if self._closed:
                return
            # Set bar to full
            self._set_total_frames(10)
            self._set_current_frame_nr(11)
            # Open directory when finished
            startfile(self.path)
            self._remove_task(self)
        except Exception as e:
            exception(e)

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
        info('Convert videos')
        files = [x for x in self.files if Path(x).suffix not in image_types]
        info(f'Convert videos: {files}')
        # Load videos
        for file_input in files:
            info(f'Convert: {file_input}')
            file_input = Path(self.path, file_input)
            info(f'Convert File: {file_input}')
            # Convert the video
            self._set_total_frames(self._get_duration(file_input) * self._get_video_fps(file_input))
            info('Frames set')
            self._run_command(file_input,
                              f'_{file_input.stem}_[{format_time(self.start_time)}_{format_time(self.end_time)}]')

    # TODO downmix
    # https://superuser.com/questions/852400/properly-downmix-5-1-to-stereo-using-ffmpeg

    def _run_command(self, file_input: Path, file_output: str):
        """
        Check file paths, and run the command with file_input and file_output
        :param file_input: Input file
        :param command: Conversion command
        :param file_output: Output file
        """
        info(f'_run_command {file_input} {file_output}')
        with self._closed_semaphore:
            if self._closed:
                return
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
            info(f'{command}')
            command = [ffmpeg_path,
                       '-sn' if not self.input_framerate else '',  # '-sn' Automatic stream selection
                       ' -r ' + self.input_framerate if self.input_framerate else '',
                       '-ss ' + start_s if self.start_time != zero_time and not self.input_framerate else '',
                       # Seeking on input file_input is faster https://trac.ffmpeg.org/wiki/Seeking
                       f'-i "{file_input}"',
                       '-ss 0.' + start_ms if self.start_time != zero_time and not self.input_framerate else '',
                       '-to ' + str(strptime(self.end_time, time_format) - strptime(start_s + '.0', time_format))
                       if self.end_time != zero_time and not self.input_framerate else '',
                       # Cut to end if no input is given
                       self.get_audio_option(file_input),
                       command.replace('<crf>', self.webm_input).replace('<res>', self.scale_input),
                       f'-subtitles="{file_input}"' if self.hardsub else '',
                       f'"{file_output}"'
                       ]

            # Start process
            self._current_file = file_output
            self._process = Popen(' '.join(command), shell=False, stdout=PIPE, stderr=STDOUT)
        self._monitor_process(self._process)
        with self._closed_semaphore:
            self._current_file = None

    def get_audio_option(self, file_input):
        """
        Get the audio command, don't convert if original audio matches selected option
        :param file_input:
        :return:
        """
        data = getoutput(audio_codec_command % file_input)
        data = json.loads(data)
        streams = data.get("streams", [])
        # Extract codec name and language
        audio_info = [
            {
                "index": stream.get("index"),
                "codec": stream.get("codec_name"),
                "language": stream.get("tags", {}).get("language", "unknown")
            }
            for stream in streams
        ]

        # Default is first stream
        audio_codec = audio_info[0]["codec"]
        index = 0

        if len(audio_info) > 1:
            for i, stream in enumerate(audio_info):
                if stream["language"] == "jpn":
                    audio_codec = stream["codec"]
                    index = i
        selection = original_audio if audio_codec == self.audio_selection else self.audio_selection
        audio_command = audio_options[selection].replace("<audio>", str(index))
        return audio_command

    def stop(self):
        """
        Stop active converter thread, delete unfinished file
        """
        with self._closed_semaphore:
            if self._closed:
                return
            self._closed = True

            if self._process:
                self._process.terminate()
                self._process.wait()  # Wait for termination
                self._current_file.unlink()

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
        info(f'FFMPEG RETURN: {result}')

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
        info(f'Get FPS {output}')
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
                info(f'GET FPS FAIL {output}')

        info(f'UNKNOWN FRAMERATE VALUE {output}')
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
