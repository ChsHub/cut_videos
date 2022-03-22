from logger_default import Logger

from cut_videos.resources.gui_texts import app
from cut_videos.view.window import Window

if __name__ == "__main__":
    with Logger(debug=True):
        frame = Window()
        frame.Show()
        app.MainLoop()
