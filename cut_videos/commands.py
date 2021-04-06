video_options = {
    'WEBM': (
        ' -sn -lavfi "scale=<res>" -c:v libvpx-vp9 -speed 0 -crf <crf> -b:v 0 -threads 2 -tile-columns 6 -frame-parallel 1 -auto-alt-ref 1 -lag-in-frames 25',
        ".webm"),
    'MP4': ('-async 1 -lavfi "scale=<res>" -c:v libx264 -profile:v main -level:v 3.2 -pix_fmt yuv420p', ".mp4"),
    'FRAMES': ('', '/%03d.png'),
    'gif': '',
    'COPY': ('-map 0:v:0 -c:v copy', '%ext')}

audio_options = {'opus': '-c:a libopus -vbr on -b:a 100k',
                               'no audio': '-an',
                               'Native format': '-c:a copy',
                               'mp3': '-c:a libmp3lame -qscale:a 3',
                               'aac': '-c:a aac -b:a 160k'}
image_types = ('.bmp', '.png', '.jpg', '.webp')