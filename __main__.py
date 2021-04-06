from logging import info
from os.path import exists
from cut_videos.paths import ffmpeg_path, ffprobe_path
from logger_default import Logger
from wx import App

from cut_videos.view.window import Window

if __name__ == "__main__":
    with Logger():
        if not exists(ffmpeg_path) or not exists(ffprobe_path):
            info('ffmpeg not found')
            raise FileNotFoundError

        app = App(False)
        frame = Window()
        frame.Show()
        app.MainLoop()
