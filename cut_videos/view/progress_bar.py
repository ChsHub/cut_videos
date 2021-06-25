from wx import Gauge


class ProgressBar(Gauge):

    def set_current_frame_nr(self, frame_nr):
        self.SetValue(int(frame_nr))
        self.Update()

    def set_total_frames(self, total_frames: int):
        if total_frames <= 0:
            raise ValueError
        self.SetValue(0)
        self.SetRange(int(total_frames))
