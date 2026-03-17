import os
import mimetypes
import re
from flask import Flask, render_template, abort, send_file, request, Response

app = Flask(__name__)

FILMS_FOLDER = os.path.join(os.path.dirname(__file__), 'films')

def get_video_files():
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
    files = []
    if os.path.exists(FILMS_FOLDER):
        for f in os.listdir(FILMS_FOLDER):
            if any(f.lower().endswith(ext) for ext in video_extensions):
                files.append(f)
    return sorted(files)

def get_mime_type(filename):
    mime, _ = mimetypes.guess_type(filename)
    return mime or 'application/octet-stream'

def is_youtube_url(url):
    return re.search(r'(youtube\.com|youtu\.be)', url, re.I) is not None

def is_vimeo_url(url):
    return 'vimeo.com' in url.lower()

def is_direct_video(url):
    video_ext = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.ogg', '.m4v')
    return any(url.lower().endswith(ext) for ext in video_ext)

@app.route('/')
def index():
    films = get_video_files()
    return render_template('index.html', films=films)

@app.route('/play-url')
def play_url_form():
    return render_template('play_url.html')

@app.route('/watch-url')
def watch_url():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    if is_youtube_url(url):
        video_id = None
        if 'youtube.com/watch' in url:
            match = re.search(r'[?&]v=([^&]+)', url)
            if match:
                video_id = match.group(1)
        elif 'youtu.be/' in url:
            match = re.search(r'youtu\.be/([^?&]+)', url)
            if match:
                video_id = match.group(1)
        if video_id:
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            return render_template('embed.html', embed_url=embed_url, type='youtube', original_url=url)
        else:
            return "Invalid YouTube URL", 400
    elif is_vimeo_url(url):
        match = re.search(r'vimeo\.com/(\d+)', url)
        if match:
            video_id = match.group(1)
            embed_url = f"https://player.vimeo.com/video/{video_id}"
            return render_template('embed.html', embed_url=embed_url, type='vimeo', original_url=url)
        else:
            return "Invalid Vimeo URL", 400
    elif is_direct_video(url):
        return render_template('direct_video.html', video_url=url)
    else:
        # Fallback: try video tag anyway
        return render_template('direct_video.html', video_url=url)

@app.route('/watch/<filename>')
def watch(filename):
    filepath = os.path.join(FILMS_FOLDER, filename)
    if not os.path.exists(filepath):
        abort(404)

    if request.args.get('download') == '1':
        mime = get_mime_type(filename)
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype=mime)

    size = os.path.getsize(filepath)
    range_header = request.headers.get('Range', None)
    if range_header:
        byte1, byte2 = 0, None
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            byte1 = int(match.group(1))
            if match.group(2):
                byte2 = int(match.group(2))
        if byte2 is None:
            byte2 = size - 1
        length = byte2 - byte1 + 1

        with open(filepath, 'rb') as f:
            f.seek(byte1)
            data = f.read(length)

        resp = Response(data, 206, mimetype=get_mime_type(filename),
                        content_type='video/' + filename.split('.')[-1])
        resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
        resp.headers.add('Accept-Ranges', 'bytes')
        resp.headers.add('Content-Length', str(length))
        return resp
    else:
        return send_file(filepath, mimetype=get_mime_type(filename))

@app.route('/films/<filename>')
def download(filename):
    return watch(filename, download=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
