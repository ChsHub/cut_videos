from logging import info

from wx import Panel, BoxSizer, VERTICAL, Font, Frame, ID_ANY, EXPAND, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, \
    NORMAL, MODERN, GA_HORIZONTAL, Gauge
from wxwidgets import FileInput, SimpleButton

from cut_videos.model.task import Task
from cut_videos.model.task_gif import TaskGif
from cut_videos.view.widgets import StandardSelection, SimpleInput, TimeInput


class Window(Frame):
    def __init__(self):
        self._files = []
        self._path = None

        # init window
        Frame.__init__(self, None, ID_ANY, "CUT", size=(800, 800))
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        loc = Icon()
        loc.CopyFromBitmap(Bitmap('icon.ico', BITMAP_TYPE_ANY))
        self.SetIcon(loc)
        panel = Panel(self, EXPAND)
        sizer = BoxSizer(VERTICAL)
        sizer.Add(FileInput(panel, text_button="Open File", callback=self._set_file,
                            file_type="*.mkv;*.mp4;*.mov;*.webm;*.avi;*.bmp;*.wmv;*.gif;*.png;*.jpg;",
                            text_title="OPEN", text_open_file="File"), 1, EXPAND)

        self._progress_bar = Gauge(panel, style=GA_HORIZONTAL)

        #  Create Input fields
        self._start_input = TimeInput(panel, label='START', initial='00:00:00.0')
        self._end_input = TimeInput(panel, label='END', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='36')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='')

        # Create check inputs
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')

        self._audio_options = {'opus': '-c:a libopus -vbr on -b:a 100k',
                               'no audio': '-an',
                               'Native format': '-c:a copy',
                               'mp3': '-c:a libmp3lame -qscale:a 3',
                               'aac': '-c:a aac -b:a 160k'}
        self._audio_select = StandardSelection(parent=panel, options=list(self._audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        self._video_options = {
            'WEBM': (
                ' -sn -lavfi "scale=%scale" -c:v libvpx-vp9 -speed 0 -crf %crf -b:v 0 -threads 2 -tile-columns 6 -frame-parallel 1 -auto-alt-ref 1 -lag-in-frames 25',
                ".webm"),
            'MP4': ('-async 1 -lavfi "scale=%scale" -c:v libx264 -profile:v main -level:v 3.2 -pix_fmt yuv420p', ".mp4"),
            'FRAMES': ('', '/%03d.png'),
            'gif': '',
            'COPY': ('-map 0:v:0 -c:v copy', '%ext')}
        self._video_select = StandardSelection(parent=panel, options=list(self._video_options.keys()),
                                               callback=None,
                                               title='Video format')

        sizer.Add(self._video_select, 1, EXPAND)
        sizer.Add(self._audio_select, 1, EXPAND)
        # Add inputs to sizer
        sizer.Add(self._start_input, 1, EXPAND)
        sizer.Add(self._end_input, 1, EXPAND)
        sizer.Add(self._scale_input, 1, EXPAND)
        sizer.Add(self._webm_input, 1, EXPAND)
        sizer.Add(self._framerate_input, 1, EXPAND)

        sizer.Add(self._progress_bar, 0, EXPAND)

        # Add Button
        sizer.Add(SimpleButton(panel, text_button='CUT', callback=self._submit_task), 1, EXPAND)
        panel.SetSizer(sizer)

    def _set_file(self, path, files):
        self._path = path
        self._files = files

    def _submit_task(self, event):
        info('START TASK')
        if self._video_select.get_selection() == 'gif':
            TaskGif(self, self._start_input.get_value()).start()
        else:
            Task(self, self._start_input.get_value()).start()
