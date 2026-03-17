# Film Streamer

A simple web application to stream or download video files (films) from a local folder, **plus play any video URL** (direct links or YouTube/Vimeo).

## Features
- Lists all video files in the `films/` directory.
- Streams local videos with seeking support.
- Direct download links.
- **Play any URL**: paste a direct video link or YouTube/Vimeo URL.
- Containerized with Docker.

## Usage

### Without Docker
1. Install Python 3.11+ and pip.
2. Install dependencies: `pip install -r requirements.txt`
3. Place your video files in the `films/` folder.
4. Run: `python app.py`
5. Open http://localhost:5000

### With Docker
1. Install Docker.
2. Place your video files in the `films/` folder.
3. Run `./run.sh` (or manually: `docker build -t film-streamer .` and `docker run -p 5000:5000 -v $(pwd)/films:/app/films film-streamer`)
4. Open http://localhost:5000

### Playing a URL
- Click "Play video from URL" on the homepage.
- Enter a direct video link (e.g., `https://example.com/video.mp4`) or a YouTube/Vimeo link.
- The video will be embedded or played with the HTML5 video tag.

## Notes
- Local videos: only files with extensions `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm` are shown.
- Streaming supports seeking via HTTP range requests.
- External URLs may be subject to CORS restrictions; some sites may not allow embedding.
- This is intended for personal use with legally owned content.
