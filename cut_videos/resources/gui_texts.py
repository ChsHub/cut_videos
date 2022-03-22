from wx import Font, MODERN, NORMAL

window_title = 'cut videos'
file_input_button = 'Open File'
file_input_title = 'Select Video File'
text_open_file = 'File'
end_input_text = 'End'
start_input_text = 'Start'
frame_rate_text = 'Input frame rate'
webm_setting_text = 'webm Quality'
video_scale_text = 'Width:Height'
clone_time_text = 'Clone time'
video_codec_text = 'File format'
audio_codec_text = 'Audio codec'
# Video format selections
gif_text = 'gif'
original_text = 'original'
mp4_text = 'mp4'
webm_text = 'webm'
frames_text = 'frames'
# Audio codec selections
original_audio = 'original'

# App needs to be started before creation of font
from wx import App
app = App(False)
window_font = Font(20, MODERN, NORMAL, NORMAL, False, 'Consolas')
