from cut_videos.resources.gui_texts import *
from cut_videos.resources.paths import ffprobe_path

video_options = {
    webm_text: ('-filter_complex "scale=<res>" -c:v libvpx-vp9 -speed 0 -crf <crf> -b:v 0 -threads 2 -tile-columns 6 -frame-parallel 1 -auto-alt-ref 1 -lag-in-frames 25', ".webm"),
    mp4_text: ('-filter_complex "scale=<res>" -c:v libx264 -profile:v main -level:v 3.2 -pix_fmt yuv420p', ".mp4"),
    frames_text: ('', '/%06d.png'),
    png_text: ('-filter_complex "scale=<res>" -plays 0', '.apng'),
    webp_text: ('-filter_complex "scale=<res>" -c:v libwebp -lossless 0 -compression_level 3 -q:v 70 -loop 0 -preset picture -vsync 0', '.webp'),
    original_text: ('-map 0:v:0 -c:v copy', '%ext')}

audio_options = {'opus': '-c:a libopus -vbr on -b:a 100k',
                 'no audio': '-an',
                 original_audio: '-map 0:a:0 -c:a copy',
                 'mp3': '-c:a libmp3lame -qscale:a 3',
                 'aac': '-c:a aac -b:a 160k'}

image_types = ('.bmp', '.png', '.jpg', '.webp')

audio_codec_command = f'{ffprobe_path} -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "%s"'
duration_command = f'{ffprobe_path} -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -sexagesimal "%s"'
fps_command = f'{ffprobe_path} -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "%s"'
frame_input_ext = '.jpg'
digits = 6
