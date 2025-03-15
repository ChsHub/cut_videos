from logger_default import Logger
from multiprocessing import freeze_support
from src.resources.gui_texts import app
from src.view.window import Window

if __name__ == "__main__":
    with Logger(debug=True):
        freeze_support()
        frame = Window()
        frame.Show()
        app.MainLoop()
