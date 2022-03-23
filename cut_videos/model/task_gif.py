from logging import error
from os.path import exists
from tempfile import TemporaryDirectory

from cut_videos.model.task import Task
from cut_videos.resources.commands import palette_command, gif_command


class TaskGif(Task):
    def _convert(self, i_file, o_file):
        with TemporaryDirectory() as palette_dir:
            # Generate palette
            palette = palette_dir + '/palette.png'
            self._run_command(file=i_file,
                              command=palette_command,
                              new_file=palette)
            if not exists(palette):
                error('No Palette')
                return
            self._run_command(file=i_file + '" -i "' + palette,
                              command=gif_command,
                              new_file=o_file + '.gif')
