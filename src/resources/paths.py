from logging import error
from pathlib import Path

ffmpeg_path = Path(Path(__file__).parent, "ffmpeg-6.0-full_build\\bin\\ffmpeg.exe")
ffprobe_path = Path(Path(__file__).parent, "ffmpeg-6.0-full_build\\bin\\ffprobe.exe")
if not ffmpeg_path.exists() or not ffprobe_path.exists():
    error('ffmpeg not found')
    raise FileNotFoundError

ffmpeg_path = str(ffmpeg_path)
ffprobe_path = str(ffprobe_path)
file_exts = "*.mkv;*.mp4;*.mov;*.webm;*.avi;*.bmp;*.wmv;*.m2ts;*.ts;*.gif;*.png;*.jpg;"