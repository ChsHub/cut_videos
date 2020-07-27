from logging import info
from os.path import abspath, exists

from wx import Panel, BoxSizer, VERTICAL, Font, Frame, ID_ANY, EXPAND, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, \
    NORMAL, MODERN, GA_HORIZONTAL, Gauge
from wxwidgets import FileInput, SimpleButton

from cut_videos.model.task import Task
from cut_videos.model.task_gif import TaskGif
from cut_videos.view.widgets import StandardSelection, SimpleInput


class Window(Frame):
    def __init__(self):
        self._files = []
        self._path = None
        self._ffmpeg_path = abspath('lib\\ffmpeg\\bin\\ffmpeg.exe')
        self._ffprobe_path = abspath('lib\\ffmpeg\\bin\\ffprobe.exe')

        if not exists(self._ffmpeg_path) or not exists(self._ffprobe_path):
            info('ffmpeg not found')
            raise FileNotFoundError

        # init window
        Frame.__init__(self, None, ID_ANY, "CUT", size=(800, 800))
        self.Bind(EVT_CLOSE, lambda x: self.Destroy())
        loc = Icon()
        loc.CopyFromBitmap(Bitmap('icon.ico', BITMAP_TYPE_ANY))
        self.SetIcon(loc)
        panel = Panel(self, EXPAND)
        sizer = BoxSizer(VERTICAL)
        sizer.Add(FileInput(panel, text_button="Open File", callback=self._set_file,
                            file_type="*.mkv;*.mp4;*.webm;*.avi;*.bmp;*.wmv;*.gif;*.png;*.jpg;",
                            text_title="OPEN", text_open_file="File"), 1, EXPAND)

        self._progress_bar = Gauge(panel, style=GA_HORIZONTAL)

        #  Create Input fields
        self._start_input = SimpleInput(panel, label='START', initial='00:00:00.0')
        self._end_input = SimpleInput(panel, label='END', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='36')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='')

        # Create check inputs
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')

        self._audio_options = {'opus': '-c:a libopus -vbr on -b:a 128k',
                               'no audio': '-an',
                               'mp3': '-c:a libmp3lame -qscale:a 3',
                               'Native format': '-c:a copy'}
        self._audio_select = StandardSelection(parent=panel, options=list(self._audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        self._video_options = {
            'WEBM': (
                ' -lavfi "scale=%scale" -c:v libvpx-vp9 -speed 0 -crf %crf -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 -auto-alt-ref 1 -lag-in-frames 25',
                ".webm"),
            'MP4': ('-async 1 -lavfi "scale=%scale"', ".mp4"),
            'FRAMES': ('', '/%03d.png'),
            'gif': '',
            'COPY': ('-c copy', '%ext')}
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
            TaskGif(self).start()
        else:
            Task(self).start()
