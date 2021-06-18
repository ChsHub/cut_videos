from logging import info

from wx import Panel, BoxSizer, VERTICAL, Font, Frame, ID_ANY, EXPAND, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, \
    NORMAL, MODERN, GA_HORIZONTAL, Gauge
from wxwidgets import FileInput, SimpleButton

from cut_videos.commands import video_options, audio_options
from cut_videos.model.task import Task
from cut_videos.model.task_gif import TaskGif
from cut_videos.view.widgets import StandardSelection, SimpleInput, TimeInput


class Window(Frame):
    def __init__(self):
        self.files = []
        self.path = None

        # init window
        Frame.__init__(self, None, ID_ANY, "CUT", size=(688, 800))
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        loc = Icon()
        loc.CopyFromBitmap(Bitmap('icon.ico', BITMAP_TYPE_ANY))
        self.SetIcon(loc)
        self.panel = Panel(self, EXPAND)
        self.sizer = BoxSizer(VERTICAL)
        self.sizer.Add(FileInput(self.panel, text_button="Open File", callback=self._set_file,
                                 file_type="*.mkv;*.mp4;*.mov;*.webm;*.avi;*.bmp;*.wmv;*.m2ts;*.gif;*.png;*.jpg;",
                                 text_title="OPEN", text_open_file="File"), 1, EXPAND)

        #  Create Input fields
        self._start_input = TimeInput(self.panel, label='START')
        self._end_input = TimeInput(self.panel, label='END')
        self._scale_input = SimpleInput(self.panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(self.panel, label='WEBM Quality', initial='36')
        self._framerate_input = SimpleInput(self.panel, label='INPUT FRAMES FRAMERATE', initial='')

        # Create check inputs
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')

        self._audio_select = StandardSelection(parent=self.panel, options=list(audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        self._video_select = StandardSelection(parent=self.panel, options=list(video_options.keys()),
                                               callback=None,
                                               title='Video format')

        # Add inputs to self.sizer
        self.sizer.Add(self._video_select, 1, EXPAND)
        self.sizer.Add(self._audio_select, 1, EXPAND)
        self.sizer.Add(self._start_input, 1, EXPAND)
        self.sizer.Add(self._end_input, 1, EXPAND)
        self.sizer.Add(self._scale_input, 1, EXPAND)
        self.sizer.Add(self._webm_input, 1, EXPAND)
        self.sizer.Add(self._framerate_input, 1, EXPAND)

        # Add Button
        self.sizer.Add(SimpleButton(self.panel, text_button='CUT', callback=self._submit_task), 1, EXPAND)
        self.panel.SetSizer(self.sizer)

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

    def _set_file(self, path, files):
        self.path = path
        self.files = files

    def set_current_frame_nr(self, frame_nr):
        self._progress_bar.SetValue(int(frame_nr))
        self._progress_bar.Update()

    def set_total_frames(self, total_frames: int):
        if total_frames <= 0:
            raise ValueError
        self._progress_bar.SetValue(0)
        self._progress_bar.SetRange(int(total_frames))

    def _add_progress_bar(self):
        self._progress_bar = Gauge(self.panel, style=GA_HORIZONTAL)
        self.sizer.Add(self._progress_bar, 0, EXPAND)
        self.Size = (self.Size[0], self.Size[1] + 20) # Enlarge window to fit new progress bar
        self.Update()

    def _submit_task(self, event):
        info('START TASK')
        self._add_progress_bar()
        task = Task

        if self._video_select.get_selection() == 'gif':
            task = TaskGif

        task(self).start()
