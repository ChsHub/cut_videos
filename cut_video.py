from logging import info

from utility.logger import Logger
from utility.os_interface import exists, get_absolute_path
from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font, Frame, \
    ID_ANY, App, EXPAND, HORIZONTAL, EVT_CLOSE, CheckBox, Icon, Bitmap, BITMAP_TYPE_ANY, NORMAL, MODERN, TextCtrl, \
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

        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        self._text_input.SetFont(font)
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input, 1, EXPAND)

        text = StaticText(self, label=label)
        text.SetFont(font)
        sizer.Add(text, 1, EXPAND)
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()


class Window(Frame):
    _files = []
    _path = None
    _ffmpeg_path = get_absolute_path('lib\\ffmpeg\\bin\\ffmpeg.exe')

    def __init__(self):

        if not exists(self._ffmpeg_path):
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
                            file_type="*.mkv;*.mp4;*.webm;*.avi;*.bmp;*.gif;*.png;*.jpg;",
                            text_title="OPEN", text_open_file="File"), 1, EXPAND)

        self._progress_bar = Gauge(panel, style=GA_HORIZONTAL)

        #  Create Input fields
        self._start_input = SimpleInput(panel, label='START', initial='00:00:00.0')
        self._end_input = SimpleInput(panel, label='END', initial='00:00:00.0')
        self._scale_input = SimpleInput(panel, label='Width:Height', initial='-1:-1')
        self._webm_input = SimpleInput(panel, label='WEBM Quality', initial='33')
        self._framerate_input = SimpleInput(panel, label='INPUT FRAMES FRAMERATE', initial='24')

        # Create check inputs
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        self.checks = []
        self.checks.append(CheckBox(panel, label="WEBM"))
        self.checks.append(CheckBox(panel, label="MP4"))
        self.checks.append(CheckBox(panel, label="FRAMES"))
        self._check_gif = CheckBox(panel, label="gif")
        self._check_gif.SetFont(font)

        self._audio_options = {'Native format': '-c:a copy', 'no audio': '-an',
                               'opus': '-c:a libopus -vbr on -b:a 128k'}
        self._audio_select = StandardSelection(parent=panel, options=list(self._audio_options.keys()),
                                               callback=None,
                                               title='Audio codec')

        # Add inputs to sizer
        sizer.Add(self._start_input, 1, EXPAND)
        sizer.Add(self._end_input, 1, EXPAND)
        sizer.Add(self._scale_input, 1, EXPAND)
        sizer.Add(self._webm_input, 1, EXPAND)
        sizer.Add(self._framerate_input, 1, EXPAND)

        sizer.Add(self._audio_select, 1, EXPAND)
        for check in self.checks:
            check.SetFont(font)
            sizer.Add(check, 1, EXPAND)
        sizer.Add(self._check_gif, 1, EXPAND)
        sizer.Add(self._progress_bar, 0, EXPAND)

        # Add Button
        sizer.Add(SimpleButton(panel, text_button='CUT', callback=self._submit_task), 1, EXPAND)
        panel.SetSizer(sizer)

    def _set_file(self, path, files):
        self._path = path
        self._files = files

    def _submit_task(self, event):
        Task(self).start()


if __name__ == "__main__":
    with Logger():
        app = App(False)
        frame = Window()
        frame.Show()
        app.MainLoop()
