from wx import Font, MODERN, NORMAL

window_title = 'cut videos'
file_input_button = 'Open File'
file_input_title = 'Select Video File'
text_open_file = 'File'
end_input_text = 'End'
start_input_text = 'Start'
frame_rate_text = 'Input frame rate'
webm_setting_text = 'webm Quality'
video_width_text = 'Width'
video_height_text = 'Height'
clone_time_text = 'Clone time'
video_codec_text = 'File format'
audio_codec_text = 'Audio codec'
# Video format selections
original_text = 'original'
mp4_text = 'mp4'
webm_text = 'webm'
webp_text = 'webp'
png_text = 'apng'
frames_text = 'frames'
# Audio codec selections
original_audio = 'original'

# App needs to be started before creation of font
from wx import App
app = App(False)
window_font = Font(20, MODERN, NORMAL, NORMAL, False, 'Consolas')
h1_font = Font(40, MODERN, NORMAL, NORMAL, False, u'Consolas')
background_color =  ( 35,  35,  40)  # (50, 50, 50, 255)
selected_color =    ( 70,  70,  85)
hover_color =       ( 70,  70,  70)  # TODO Set mouse over color
text_color =        (255, 255, 255)
text_color_header = (100, 100, 100)
icon_path = 'icon.ico'
