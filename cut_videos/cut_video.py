from logging import info
from os.path import abspath, exists

from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font, Frame, \
    ID_ANY, EXPAND, HORIZONTAL, EVT_CLOSE, Icon, Bitmap, BITMAP_TYPE_ANY, NORMAL, MODERN, TextCtrl, \
    GA_HORIZONTAL, Gauge
from wxwidgets import FileInput, SimpleButton

from cut_videos.model.task import Task


class StandardSelection(Panel):
    def __init__(self, parent, callback, title, options):
        super().__init__(parent)

        sizer = BoxSizer(VERTICAL)
        text = StaticText(self, label=title)
        sizer.Add(text)
        self.selection = ComboBox(self, style=CB_DROPDOWN | CB_READONLY, choices=options)
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        text.SetFont(font)
        self.selection.SetFont(font)
        # self.selection.SetFont(font)
        self.selection.SetValue(options[0])
        if callback:
            self.selection.Bind(EVT_TEXT, lambda x: callback(self.selection.GetValue()))
        sizer.Add(self.selection, 1, EXPAND)
        self.SetSizer(sizer)

    def get_selection(self):
        return self.selection.GetValue()


class SimpleInput(Panel):

    def __init__(self, parent, label, initial=""):
        super().__init__(parent)

        sizer = BoxSizer(HORIZONTAL)
        self._text_input = TextCtrl(self)
        self._text_input.SetFont(Font(40, MODERN, NORMAL, NORMAL, False, u'Consolas'))
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input, 1, EXPAND)

        text = StaticText(self, label=label)
        text.SetFont(Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas'))
        sizer.Add(text, 1, EXPAND)
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()


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

        self._audio_options = {'Native format': '-c:a copy', 'no audio': '-an',
                               'opus': '-c:a libopus -vbr on -b:a 128k'}
        self._audio_select = StandardSelection(parent=panel, options=list(self._audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        self._video_options = {
            'WEBM': (
                ' -lavfi "scale=%scale" -c:v libvpx-vp9 -speed 0 -crf %crf -b:v 0 -threads 8 -tile-columns 6 -frame-parallel 1 -auto-alt-ref 1 -lag-in-frames 25',
                ".webm"),
            'MP4': ('-async 1 -lavfi "scale=%scale"', ".mp4"), 'FRAMES': ('', '/%03d.png'), 'gif': '',
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
        Task(self).start()
