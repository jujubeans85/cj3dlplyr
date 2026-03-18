import os
import mimetypes
import re
import requests
import json
from flask import Flask, render_template, abort, send_file, request, Response, jsonify
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

FILMS_FOLDER = os.path.join(os.path.dirname(__file__), 'films')

# ========== EXISTING FUNCTIONS ==========
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

# ========== NEW: CORS PROXY ==========
@app.route('/proxy')
def proxy():
    """CORS proxy for streaming external video files"""
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    try:
        # Fetch the remote content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Handle range requests for video seeking
        range_header = request.headers.get('Range')
        if range_header:
            headers['Range'] = range_header
        
        resp = requests.get(url, headers=headers, stream=True)
        
        # Create Flask response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                           if name.lower() not in excluded_headers]
        
        def generate():
            for chunk in resp.iter_content(chunk_size=4096):
                yield chunk
        
        return Response(generate(), resp.status_code, response_headers)
    
    except Exception as e:
        return f"Proxy error: {str(e)}", 500

@app.route('/proxy-m3u8')
def proxy_m3u8():
    """Special proxy for M3U8 playlists (HLS streaming)"""
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        content = resp.text
        
        # Convert relative paths in M3U8 to absolute
        base_url = url[:url.rfind('/') + 1]
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line and not line.startswith('#'):
                # This is a segment URL - make it absolute
                if not line.startswith('http'):
                    lines[i] = urljoin(base_url, line)
        
        modified_content = '\n'.join(lines)
        
        response = Response(modified_content, content_type='application/vnd.apple.mpegurl')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        return f"Proxy error: {str(e)}", 500

# ========== NEW: TORRENT SEARCH (YTS) ==========
@app.route('/torrents')
def torrent_search_form():
    """Display torrent search form"""
    return render_template('torrent_search.html')

@app.route('/torrents/search')
def torrent_search():
    """Search for movies on YTS"""
    query = request.args.get('q', '')
    if not query:
        return render_template('torrent_results.html', error="Please enter a search term", results=[])
    
    try:
        # Using YTS public API
        url = f"https://yts.mx/api/v2/list_movies.json"
        params = {
            'query_term': query,
            'sort_by': 'seeds',
            'order_by': 'desc',
            'limit': 20
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'ok' and data['data']['movie_count'] > 0:
            movies = data['data']['movies']
            
            # Process movies to extract torrent info
            results = []
            for movie in movies:
                movie_data = {
                    'title': movie['title'],
                    'year': movie.get('year', ''),
                    'rating': movie.get('rating', 0),
                    'cover': movie.get('medium_cover_image', ''),
                    'synopsis': movie.get('synopsis', '')[:200] + '...' if movie.get('synopsis') else '',
                    'torrents': []
                }
                
                # Get best quality torrents
                for torrent in movie.get('torrents', [])[:2]:  # Limit to 2 best
                    movie_data['torrents'].append({
                        'quality': torrent['quality'],
                        'size': torrent['size'],
                        'seeds': torrent['seeds'],
                        'peers': torrent['peers'],
                        'url': torrent['url'],
                        'hash': torrent['hash']
                    })
                
                results.append(movie_data)
            
            return render_template('torrent_results.html', results=results, query=query)
        else:
            return render_template('torrent_results.html', error="No movies found", results=[], query=query)
    
    except Exception as e:
        return render_template('torrent_results.html', error=f"Search failed: {str(e)}", results=[], query=query)

# ========== NEW: FREE STREAMING SERVICES ==========
@app.route('/free-streaming')
def free_streaming():
    """Display free streaming services information"""
    return render_template('free_streaming.html')

@app.route('/api/streaming-availability')
def streaming_availability():
    """Proxy for Streaming Availability API [citation:3]"""
    title = request.args.get('title', '')
    country = request.args.get('country', 'us')
    
    if not title:
        return jsonify({'error': 'No title provided'}), 400
    
    try:
        # Using the free tier of Streaming Availability API via RapidAPI
        # Sign up at https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability/
        
        # For demo purposes, we'll return mock data that matches the real API structure
        # In production, replace with actual API call
        
        # This is a sample of what the real API returns [citation:3]
        mock_data = {
            "result": [
                {
                    "title": title,
                    "year": "2023",
                    "streamingInfo": {
                        "us": {
                            "netflix": [{"link": "https://www.netflix.com/title/sample", "quality": "HD"}],
                            "hulu": [{"link": "https://www.hulu.com/movie/sample", "quality": "HD"}],
                            "prime": [{"link": "https://www.primevideo.com/detail/sample", "quality": "UHD"}]
                        }
                    }
                }
            ]
        }
        
        return jsonify(mock_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== EXISTING ROUTES (UPDATED WITH PROXY) ==========
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

    # Use proxy for CORS issues
    proxy_url = f"/proxy?url={requests.utils.quote(url)}"
    
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
        # Use proxy for direct videos to bypass CORS [citation:1][citation:5]
        return render_template('direct_video_proxy.html', video_url=url, proxy_url=proxy_url)
    else:
        # Try proxy for unknown formats
        return render_template('direct_video_proxy.html', video_url=url, proxy_url=proxy_url)

@app.route('/watch/<filename>')
def watch(filename):
    # ... (existing watch function remains unchanged) ...
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
