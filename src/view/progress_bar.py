from wx import Gauge


class ProgressBar(Gauge):

    def set_current_frame_nr(self, frame_nr):
        self.SetValue(int(frame_nr))
        self.Update()

    def set_total_frames(self, total_frames: int):
        if total_frames <= 0:
            raise ValueError
        self.SetRange(int(total_frames * 1.1))  # Set frame count 10% higher
