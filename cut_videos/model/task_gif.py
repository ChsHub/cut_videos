from logging import info, error
from os.path import exists
from tempfile import TemporaryDirectory

from timerpy import Timer

from cut_videos.model.task import Task


class TaskGif(Task):
    def _convert(self, i_file, o_file, frame_count):
        self._set_total_frames(frame_count)
        with TemporaryDirectory() as palette_dir:
            # generate palette
            with Timer('GENERATE PALETTE', log_function=info):
                palette = palette_dir + '/palette.png'
                self._run_command(file=i_file,
                                  command=' -vf "scale=<res>:flags=lanczos,palettegen"',
                                  new_file=palette)
            if not exists(palette):
                error('No Palette')
                return

            for mode, suffix in [
                (':flags=lanczos,paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle', "_bayer.gif"),
                (':flags=lanczos,paletteuse=dither=none', "_default.gif"),
                ('', '_no_pal.gif')]:
                self._run_command(file=i_file + '" -i "' + palette,
                                  command=' -lavfi "scale=<res>%s"' % mode,
                                  new_file=o_file + suffix)
