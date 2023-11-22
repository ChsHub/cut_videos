from logging import error, info
from pathlib import Path
from re import findall

from wx import Panel, BoxSizer, VERTICAL, Frame, ID_ANY, EXPAND, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, \
    GA_HORIZONTAL, CheckBox
from wxwidgets import FileInput, SimpleButton

from cut_videos.model.task import Task, unformat_time
from cut_videos.resources.commands import video_options, audio_options
from cut_videos.resources.gui_texts import *
from cut_videos.resources.paths import file_exts
from cut_videos.view.progress_bar import ProgressBar
from cut_videos.view.widgets import StandardSelection, SimpleInput, TimeInput
from send2trash import send2trash

from resources.search_paths import search_paths


class Window(Frame):
    def __init__(self):
        self.files = []
        self.path = None
        self._active_tasks = []
        # init window
        Frame.__init__(self, None, ID_ANY, window_title, size=(688, 900))
        self.SetBackgroundColour(background_color)
        # ICON
        icon = Icon()
        icon.CopyFromBitmap(Bitmap(icon_path, BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.panel = Panel(self, EXPAND)
        self._sizer = BoxSizer(VERTICAL)
        self.file_input = FileInput(self.panel, text_button=file_input_button, callback=self._set_file,
                               file_type=file_exts, text_title=file_input_title, text_open_file=text_open_file, )
        # text_color=text_color, font=window_font) TODO

        # Create Input fields
        self._start_input = TimeInput(self.panel, label=start_input_text)
        self._end_input = TimeInput(self.panel, label=end_input_text)
        self._webm_input = SimpleInput(self.panel, label=webm_setting_text, initial='36')
        self._width_input = SimpleInput(self.panel, label=video_width_text, initial='')
        self._height_input = SimpleInput(self.panel, label=video_height_text, initial='')
        self._framerate_input = SimpleInput(self.panel, label=frame_rate_text, initial='')
        self._hard_sub_check = CheckBox(self.panel, label='HARDSUBS')
        self._hard_sub_check.SetFont(font=h1_font)
        button = SimpleButton(self.panel, text_button='CUT', callback=self._submit_task)
        # Create check inputs
        self._audio_select = StandardSelection(parent=self.panel, options=list(audio_options.keys()), callback=None,
                                               title=audio_codec_text, font=window_font)
        self._video_select = StandardSelection(parent=self.panel, options=list(video_options.keys()), callback=None,
                                               title=video_codec_text, font=window_font)
        clone_time_input = FileInput(self.panel, text_button=clone_time_text, callback=self._clone_time,
                                     file_type=file_exts, text_title=file_input_title, text_open_file=text_open_file)

        # Add inputs to self._sizer
        self._sizer.Add(self.file_input, 1, EXPAND)
        self._sizer.Add(self._video_select, 1, EXPAND)
        self._sizer.Add(self._audio_select, 1, EXPAND)
        self._sizer.Add(clone_time_input, 1, EXPAND)
        self._sizer.Add(self._start_input, 1, EXPAND)
        self._sizer.Add(self._end_input, 1, EXPAND)
        self._sizer.Add(self._webm_input, 1, EXPAND)
        self._sizer.Add(self._width_input, 1, EXPAND)
        self._sizer.Add(self._height_input, 1, EXPAND)
        self._sizer.Add(self._framerate_input, 1, EXPAND)
        self._sizer.Add(self._hard_sub_check, 1)
        self._sizer.Add(button, 1, EXPAND)

        self.panel.SetSizer(self._sizer)
        queue = list(self.GetChildren())
        while queue:
            child = queue.pop()
            queue += list(child.GetChildren())
            child.SetBackgroundColour(background_color)
            child.SetForegroundColour(text_color)

        self.Bind(EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.Destroy()
        for task in self._active_tasks:
            task.stop()

    @property
    def start_time(self):
        return self._start_input.get_value()

    @property
    def end_time(self):
        return self._end_input.get_value()

    @property
    def video_selection(self):
        return self._video_select.get_selection()

    @property
    def audio_selection(self):
        return self._audio_select.get_selection()

    @property
    def input_framerate(self):
        return self._framerate_input.get_value()

    @property
    def scale_input(self):
        width = self._width_input.get_value()
        height = self._height_input.get_value()
        return f'{width if width else -1}:{height if height else -1}'

    @property
    def webm_input(self):
        return self._webm_input.get_value()

    @property
    def hardsub(self):
        return self._hard_sub_check.GetValue()

    def get_original(self, file):
        file_name = Path(findall('(.+)_', file)[0]).name

        pattern = f"**/*{file_name[-13:] if len(file_name) >= 13 else file_name}"

        for path in search_paths:
            found_files = list(Path(path).glob(pattern))
            if len(found_files) > 0:
                self.file_input._text_input.SetValue(f"{found_files[0].parent}/{found_files[0].name}")
                return self._set_file(found_files[0].parent, [found_files[0].name])

    def _clone_time(self, path, files):
        if len(files) == 1:  # Clone from video
            data = files[0]
            start, end = findall(r"\[([\d+|\-|\.]+)?_([\d+|\-|\.]+)?\]", data)[-1]
            start = unformat_time(start)
            end = unformat_time(end)

        elif len(files) == 2:  # Clone from screenshots
            start = findall(r"(\d{6}\.\d{3})", files[0])[-1].replace('.', '')
            end = findall(r"(\d{6}\.\d{3})", files[1])[-1].replace('.', '')

            send2trash(files[0])
            send2trash(files[1])
            start, end = list(sorted((start, end)))

        else:
            info("Too many input files for Time Cloning")
            return
        self.get_original(files[0])
        self._start_input.set_value(start)
        self._end_input.set_value(end)

    def _set_file(self, path, files):
        self.path = path
        self.files = files

    def _add_progress_bar(self):
        progress_bar = ProgressBar(self.panel, style=GA_HORIZONTAL)
        self._sizer.Add(progress_bar, 0, EXPAND)
        self.Size = (self.Size[0], self.Size[1] + 20)  # Enlarge window to fit new progress bar
        self.Update()
        return progress_bar

    def remove_task(self, task):
        self._active_tasks.remove(task)

    def _submit_task(self, event):
        bar = self._add_progress_bar()
        self._active_tasks.append(
            Task(self.input_framerate,
                 self.start_time,
                 self.end_time,
                 self.hardsub,
                 self.webm_input,
                 self.scale_input,
                 self.audio_selection,
                 self.video_selection,
                 self.path,
                 self.files.copy(),
                 self.remove_task,
                 bar))
