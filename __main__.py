from logger_default import Logger

from src.resources.gui_texts import app
from src.view.window import Window

if __name__ == "__main__":
    with Logger(debug=True):
        frame = Window()
        frame.Show()
        app.MainLoop()
