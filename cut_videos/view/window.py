from re import findall

from wx import Panel, BoxSizer, VERTICAL, Frame, ID_ANY, EXPAND, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, \
    GA_HORIZONTAL, CheckBox
from wxwidgets import FileInput, SimpleButton

from cut_videos.model.task import Task, unformat_time
from cut_videos.model.task_gif import TaskGif
from cut_videos.resources.commands import video_options, audio_options
from cut_videos.resources.gui_texts import *
from cut_videos.resources.paths import file_exts
from cut_videos.view.progress_bar import ProgressBar
from cut_videos.view.widgets import StandardSelection, SimpleInput, TimeInput


class Window(Frame):
    def __init__(self):
        self.files = []
        self.path = None
        # init window
        Frame.__init__(self, None, ID_ANY, window_title, size=(688, 800))
        self.SetBackgroundColour(background_color)
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        # ICON
        icon = Icon()
        icon.CopyFromBitmap(Bitmap(icon_path, BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.panel = Panel(self, EXPAND)
        self._sizer = BoxSizer(VERTICAL)
        file_input = FileInput(self.panel, text_button=file_input_button, callback=self._set_file,
                               file_type=file_exts, text_title=file_input_title, text_open_file=text_open_file,
                               text_color=text_color, font=window_font)

        # Create Input fields
        self._start_input = TimeInput(self.panel, label=start_input_text)
        self._end_input = TimeInput(self.panel, label=end_input_text)
        self._scale_input = SimpleInput(self.panel, label=video_scale_text, initial='-1:-1')
        self._webm_input = SimpleInput(self.panel, label=webm_setting_text, initial='36')
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
        self._sizer.Add(file_input, 1, EXPAND)
        self._sizer.Add(self._video_select, 1, EXPAND)
        self._sizer.Add(self._audio_select, 1, EXPAND)
        self._sizer.Add(clone_time_input, 1, EXPAND)
        self._sizer.Add(self._start_input, 1, EXPAND)
        self._sizer.Add(self._end_input, 1, EXPAND)
        self._sizer.Add(self._scale_input, 1, EXPAND)
        self._sizer.Add(self._webm_input, 1, EXPAND)
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

    @property
    def start_time(self):
        return self._start_input.get_value()

    @property
    def end_time(self):
        return self._end_input.get_value()

    @property
    def video_selection(self):
        return video_options[self._video_select.get_selection()]

    @property
    def audio_selection(self):
        return self._audio_select.get_selection()

    @property
    def input_framerate(self):
        return self._framerate_input.get_value()

    @property
    def scale_input(self):
        return self._scale_input.get_value()

    @property
    def webm_input(self):
        return self._webm_input.get_value()

    @property
    def hardsub(self):
        return self._hard_sub_check.GetValue()

    def _clone_time(self, path, files):
        data = files[-1]
        start, end = findall(r"\[([\d+|\-|\.]+)_([\d+|\-|\.]+)\]", data)[-1]
        self._start_input.set_value(unformat_time(start))
        self._end_input.set_value(unformat_time(end))

    def _set_file(self, path, files):
        self.path = path
        self.files = files

    def _add_progress_bar(self):
        progress_bar = ProgressBar(self.panel, style=GA_HORIZONTAL)
        self._sizer.Add(progress_bar, 0, EXPAND)
        self.Size = (self.Size[0], self.Size[1] + 20)  # Enlarge window to fit new progress bar
        self.Update()
        return progress_bar

    def _submit_task(self, event):
        if self._video_select.get_selection() == gif_text:
            task = TaskGif
        else:
            task = Task

        bar = self._add_progress_bar()
        task(self, bar).start()
