from logger_default import Logger
from wx import App

from cut_videos.view.window import Window

if __name__ == "__main__":
    with Logger(debug=True):
        app = App(False)
        frame = Window()
        frame.Show()
        app.MainLoop()
