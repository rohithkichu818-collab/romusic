import os
import re
import json
import time
import threading
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, Response, abort
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.utils import secure_filename

# yt-dlp as a Python library (NOT subprocess)
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from config import Config
from models import db, User, Artist, Album, Song, Playlist, RecentlyPlayed, likes

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please sign in to experience ROMUSIC."
login_manager.login_message_category = "info"

# Jinja template filters
@app.template_filter('basename')
def filter_basename(path):
    if not path:
        return ''
    return os.path.basename(path)

@app.template_filter('format_duration')
def filter_format_duration(seconds):
    if not seconds:
        return "0:00"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ---------- OPENBLAST-STYLE AUDIO STREAMING ENGINE & LRCLIB LYRICS ----------
STREAM_CACHE = {}

def get_youtube_audio_url(video_id, title=None, artist=None):
    """Extract direct audio stream URL with 2-hour in-memory cache and automatic query fallback."""
    now = time.time()
    if video_id and video_id in STREAM_CACHE:
        url, exp = STREAM_CACHE[video_id]
        if now < exp:
            return url

    if not YT_DLP_AVAILABLE:
        return None

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    # Attempt 1: Direct video ID extraction
    if video_id and video_id != 'None':
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                url = info.get('url') if info else None
                if url:
                    STREAM_CACHE[video_id] = (url, now + 7200) # Cache for 2 hours
                    return url
        except Exception as e:
            print(f"[Direct Extract Warning] video_id={video_id}: {e}")

    # Attempt 2: Fallback search by title and artist if direct extraction failed
    if title:
        try:
            search_query = f"{title} {artist or ''} audio".strip()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                entries = info.get('entries', []) if info else []
                if entries and entries[0]:
                    top = entries[0]
                    fallback_url = top.get('url')
                    fallback_id = top.get('id')
                    if fallback_url:
                        if fallback_id:
                            STREAM_CACHE[fallback_id] = (fallback_url, now + 7200)
                        if video_id:
                            STREAM_CACHE[video_id] = (fallback_url, now + 7200)
                        return fallback_url
        except Exception as e:
            print(f"[Fallback Extract Error] query={title}: {e}")

    return None


def stream_remote_audio(stream_url, client_range=None, video_id=None, title=None, artist=None):
    """Stream remote audio to client with HTTP 206 Partial Content Range support and 403 recovery."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    if client_range:
        headers['Range'] = client_range

    try:
        req = urllib.request.Request(stream_url, headers=headers)
        remote_resp = urllib.request.urlopen(req, timeout=12)
    except urllib.error.HTTPError as e:
        # If expired URL (403), evict cache and retry once
        if e.code in (403, 410) and video_id:
            STREAM_CACHE.pop(video_id, None)
            fresh_url = get_youtube_audio_url(video_id, title=title, artist=artist)
            if fresh_url and fresh_url != stream_url:
                try:
                    req = urllib.request.Request(fresh_url, headers=headers)
                    remote_resp = urllib.request.urlopen(req, timeout=12)
                except Exception:
                    return Response(status=e.code)
            else:
                return Response(status=e.code)
        else:
            return Response(status=e.code)
    except Exception as e:
        print(f"[RemoteStream Error]: {e}")
        return abort(502)

    status_code = remote_resp.status
    content_type = remote_resp.headers.get('Content-Type') or 'audio/mp4'
    content_length = remote_resp.headers.get('Content-Length')
    content_range = remote_resp.headers.get('Content-Range')

    def generate_chunks():
        try:
            chunk_size = 64 * 1024 # 64 KB chunks for snappy responsive seeking
            while True:
                chunk = remote_resp.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                remote_resp.close()
            except Exception:
                pass

    resp = Response(
        generate_chunks(),
        status=status_code,
        mimetype=content_type,
        direct_passthrough=True
    )
    resp.headers['Accept-Ranges'] = 'bytes'
    if content_length:
        resp.headers['Content-Length'] = content_length
    if content_range:
        resp.headers['Content-Range'] = content_range
    return resp


def stream_local_file(path, range_header):
    """Stream local audio file with HTTP Range support."""
    file_size = os.path.getsize(path)
    ext = os.path.splitext(path)[1].lower()
    mime_types = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.flac': 'audio/flac'
    }
    content_type = mime_types.get(ext, 'audio/mpeg')

    if not range_header:
        return send_file(path, mimetype=content_type, as_attachment=False)

    byte1, byte2 = 0, None
    m = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if m:
        g = m.groups()
        if g[0]:
            byte1 = int(g[0])
        if g[1]:
            byte2 = int(g[1])
    if byte2 is None:
        byte2 = file_size - 1

    length = byte2 - byte1 + 1

    def generate_chunks():
        with open(path, 'rb') as f:
            f.seek(byte1)
            rem = length
            chunk_size = 128 * 1024
            while rem > 0:
                chunk = f.read(min(chunk_size, rem))
                if not chunk:
                    break
                rem -= len(chunk)
                yield chunk

    resp = Response(generate_chunks(), 206, mimetype=content_type, direct_passthrough=True)
    resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
    resp.headers.add('Accept-Ranges', 'bytes')
    resp.headers.add('Content-Length', str(length))
    return resp


@app.route('/sw.js')
def service_worker():
    """Serve PWA Service Worker at root scope."""
    return send_file(os.path.join(app.root_path, 'static', 'sw.js'), mimetype='application/javascript')


@app.route('/api/stream/<song_identifier>')
def stream_audio(song_identifier):
    """
    Unified high-performance audio streaming endpoint.
    Accepts DB song ID or YouTube video ID string.
    Streams ad-free, pure crystal-clear audio with HTTP Range seek support.
    """
    range_header = request.headers.get('Range', None)
    
    # Check DB by ID or youtube_id
    song = None
    if str(song_identifier).isdigit():
        song = Song.query.get(int(song_identifier))
    if not song:
        song = Song.query.filter_by(youtube_id=str(song_identifier)).first()

    # Case 1: Local file exists and is uploaded by user
    if song and song.file_path and os.path.exists(song.file_path):
        # If not a synth wav fallback, stream local
        if not song.youtube_id or not song.file_path.endswith('.wav'):
            return stream_local_file(song.file_path, range_header)

    # Case 2: YouTube audio stream
    video_id = None
    if song and song.youtube_id:
        video_id = song.youtube_id
    elif not str(song_identifier).isdigit():
        video_id = str(song_identifier)

    title = song.title if song else request.args.get('title')
    artist = song.artist.name if (song and song.artist) else request.args.get('artist')

    stream_url = get_youtube_audio_url(video_id, title=title, artist=artist)
    if not stream_url:
        abort(404)

    return stream_remote_audio(stream_url, range_header, video_id=video_id, title=title, artist=artist)


@app.route('/api/lyrics')
def api_lyrics():
    """
    Synchronized karaoke lyrics API powered by LRCLIB.
    Auto-cleans title & artist, returns syncedLyrics + plainLyrics.
    """
    title = request.args.get('title', '').strip()
    artist = request.args.get('artist', '').strip()

    if not title:
        return jsonify({'found': False, 'synced_lyrics': None, 'plain_lyrics': None})

    # Clean title
    clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
    clean_title = re.sub(r'(?i)\b(official|video|song|lyrical|audio|full|track|hd|4k|music|remix|mix)\b', '', clean_title)
    clean_title = re.sub(r'[\s\-_\/\|]+', ' ', clean_title).strip()

    clean_artist = re.sub(r'[\(\[].*?[\)\]]', '', artist)
    clean_artist = re.sub(r'(?i)\b(vevo|official|channel|records|music)\b', '', clean_artist).strip()

    # Query LRCLIB search
    query_str = f"{clean_title} {clean_artist}".strip()
    lrclib_url = f"https://lrclib.net/api/search?q={urllib.parse.quote(query_str)}"
    headers = {'User-Agent': 'RoMusic/2.0 (Midnight Luxe Audio Platform)'}

    try:
        req = urllib.request.Request(lrclib_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and isinstance(data, list) and len(data) > 0:
                best = data[0]
                return jsonify({
                    'found': True,
                    'track_name': best.get('trackName'),
                    'artist_name': best.get('artistName'),
                    'synced_lyrics': best.get('syncedLyrics'),
                    'plain_lyrics': best.get('plainLyrics')
                })
    except Exception as e:
        print(f"[Lyrics Error]: {e}")

    return jsonify({
        'found': False,
        'track_name': clean_title,
        'artist_name': clean_artist,
        'synced_lyrics': None,
        'plain_lyrics': None
    })


# ---------- PAGES ----------
@app.route('/')
def index():
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Hero featured song
    featured_song = Song.query.filter(Song.title.ilike('%Jaada%')).first() or Song.query.first()
    
    # Sections
    recently_played = []
    if current_user.is_authenticated:
        recent_records = RecentlyPlayed.query.filter_by(user_id=current_user.id).order_by(RecentlyPlayed.played_at.desc()).limit(10).all()
        recently_played = [r.song for r in recent_records if r.song]
    if not recently_played:
        recently_played = Song.query.order_by(Song.plays_count.desc()).limit(8).all()

    trending_songs = Song.query.order_by(Song.plays_count.desc()).limit(10).all()
    
    # Language collections
    malayalam_songs = Song.query.filter_by(language='Malayalam').all()
    tamil_songs = Song.query.filter_by(language='Tamil').all()
    hindi_songs = Song.query.filter_by(language='Hindi').all()
    english_songs = Song.query.filter_by(language='English').all()
    
    # Mood collections
    midnight_drive = Song.query.filter_by(mood='Midnight Drive').all()
    aurora_chill = Song.query.filter_by(mood='Aurora').all()
    neon_focus = Song.query.filter_by(mood='Neon Focus').all()
    
    # Artists & Albums
    artists = Artist.query.limit(8).all()
    albums = Album.query.limit(8).all()
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    
    return render_template('index.html',
        featured_song=featured_song,
        recently_played=recently_played,
        trending_songs=trending_songs,
        malayalam_songs=malayalam_songs,
        tamil_songs=tamil_songs,
        hindi_songs=hindi_songs,
        english_songs=english_songs,
        midnight_drive=midnight_drive,
        aurora_chill=aurora_chill,
        neon_focus=neon_focus,
        artists=artists,
        albums=albums,
        user_playlists=user_playlists
    )

@app.route('/search')
def search_page():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    
    songs = []
    artists = []
    albums = []
    
    if query:
        songs = Song.query.filter(
            (Song.title.ilike(f"%{query}%")) |
            (Song.language.ilike(f"%{query}%")) |
            (Song.genre.ilike(f"%{query}%")) |
            (Song.mood.ilike(f"%{query}%"))
        ).all()
        artists = Artist.query.filter(Artist.name.ilike(f"%{query}%")).all()
        albums = Album.query.filter(Album.title.ilike(f"%{query}%")).all()
    elif category:
        if category in ['Malayalam', 'Tamil', 'Hindi', 'English']:
            songs = Song.query.filter_by(language=category).all()
        else:
            songs = Song.query.filter((Song.genre.ilike(f"%{category}%")) | (Song.mood.ilike(f"%{category}%"))).all()

    trending_tags = ['Malayalam Hits', 'Tamil Club', 'Hindi Soul', 'Synthwave 2026', 'Midnight Drive', 'Anirudh', 'Sushin Shyam', 'The Weeknd']

    return render_template('search.html',
        query=query,
        category=category,
        songs=songs,
        artists=artists,
        albums=albums,
        trending_tags=trending_tags
    )

@app.route('/library')
@login_required
def library_page():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    liked_songs = current_user.liked_songs
    recent_records = RecentlyPlayed.query.filter_by(user_id=current_user.id).order_by(RecentlyPlayed.played_at.desc()).limit(15).all()
    recent_songs = [r.song for r in recent_records if r.song]
    return render_template('library.html',
        playlists=playlists,
        liked_songs=liked_songs,
        recent_songs=recent_songs
    )

@app.route('/favorites')
@login_required
def favorites_page():
    songs = current_user.liked_songs
    return render_template('favorites.html', songs=songs)

@app.route('/playlist/<int:playlist_id>')
def playlist_detail(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    return render_template('playlist_detail.html', playlist=playlist)

@app.route('/artist/<int:artist_id>')
def artist_profile(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    return render_template('artist_profile.html', artist=artist)

@app.route('/album/<int:album_id>')
def album_detail(album_id):
    album = Album.query.get_or_404(album_id)
    return render_template('album_detail.html', album=album)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        cover_file = request.files.get('cover')
        title = request.form.get('title', '').strip()
        artist_name = request.form.get('artist', '').strip()
        album_name = request.form.get('album', '').strip()
        genre = request.form.get('genre', 'Electronic')
        language = request.form.get('language', 'English')
        mood = request.form.get('mood', 'Midnight Drive')
        lyrics = request.form.get('lyrics', '')

        if not file or not allowed_file(file.filename):
            flash('Please upload a valid audio file (.mp3, .wav, .ogg, .m4a, .flac).', 'error')
            return redirect(request.url)

        if not title:
            flash('Please provide a song title.', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        save_filename = f"{timestamp}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(save_path)

        # Handle Cover Artwork
        cover_url = '/static/images/covers/cover_midnight.svg'
        if cover_file and cover_file.filename:
            c_name = secure_filename(f"cover_{timestamp}_{cover_file.filename}")
            c_dir = os.path.join(app.root_path, 'static', 'images', 'covers')
            os.makedirs(c_dir, exist_ok=True)
            cover_file.save(os.path.join(c_dir, c_name))
            cover_url = f"/static/images/covers/{c_name}"

        # Artist
        artist = None
        if artist_name:
            artist = Artist.query.filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name, bio=f"Independent artist on ROMUSIC.", image_url=cover_url)
                db.session.add(artist)
                db.session.commit()

        # Album
        album = None
        if album_name and artist:
            album = Album.query.filter_by(title=album_name, artist_id=artist.id).first()
            if not album:
                album = Album(title=album_name, cover_url=cover_url, artist_id=artist.id, genre=genre, language=language)
                db.session.add(album)
                db.session.commit()

        # Create Song
        song = Song(
            title=title,
            file_path=save_path,
            cover_url=cover_url,
            duration=210,
            genre=genre,
            language=language,
            mood=mood,
            lyrics=lyrics,
            artist_id=artist.id if artist else None,
            album_id=album.id if album else None
        )
        db.session.add(song)
        db.session.commit()

        flash(f'"{title}" uploaded successfully to ROMUSIC!', 'success')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    songs = Song.query.order_by(Song.id.desc()).all()
    playlists = Playlist.query.all()
    artists = Artist.query.all()
    return render_template('admin.html',
        users=users,
        songs=songs,
        playlists=playlists,
        artists=artists
    )

@app.route('/admin/delete_song/<int:song_id>', methods=['POST'])
@login_required
def admin_delete_song(song_id):
    if not current_user.is_admin:
        abort(403)
    song = Song.query.get_or_404(song_id)
    title = song.title
    db.session.delete(song)
    db.session.commit()
    flash(f'Song "{title}" has been deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

# ---------- AUTHENTICATION ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome back to ROMUSIC, {user.username}.", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        flash("Invalid email/username or password. Please try again.", "error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(request.url)

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please pick another moniker.", "error")
            return redirect(request.url)

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Try logging in.", "error")
            return redirect(request.url)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to the Midnight Luxe experience, {username}!", "success")
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Signed out of ROMUSIC.", "info")
    return redirect(url_for('login'))


# ---------- REST APIS FOR PLAYER & DYNAMIC UI ----------
@app.route('/api/songs')
def api_songs():
    songs = Song.query.all()
    user_id = current_user.id if current_user.is_authenticated else None
    return jsonify([s.to_dict(user_id) for s in songs])

@app.route('/api/song/<int:song_id>')
def api_song(song_id):
    song = Song.query.get_or_404(song_id)
    user_id = current_user.id if current_user.is_authenticated else None
    return jsonify(song.to_dict(user_id))

def get_or_create_song(identifier, title=None, artist_name=None, cover_url=None, duration=None):
    """Retrieve existing song or dynamically create from YouTube metadata."""
    song = None
    if str(identifier).isdigit():
        song = Song.query.get(int(identifier))
    if not song:
        song = Song.query.filter_by(youtube_id=str(identifier)).first()
    
    if not song and identifier and not str(identifier).isdigit():
        video_id = str(identifier)
        t = title or f"Track {video_id}"
        a_name = artist_name or "Universal Artist"
        c_url = cover_url or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        
        artist = Artist.query.filter_by(name=a_name).first()
        if not artist:
            artist = Artist(name=a_name, bio=f"Artist on ROMUSIC.", image_url=c_url)
            db.session.add(artist)
            db.session.flush()

        song = Song(
            title=t,
            youtube_id=video_id,
            cover_url=c_url,
            duration=int(duration) if duration else 210,
            genre='Trending',
            language='Malayalam',
            mood='Midnight Drive',
            artist_id=artist.id if artist else None
        )
        db.session.add(song)
        db.session.commit()
    return song


@app.route('/api/like/<song_identifier>', methods=['POST'])
@login_required
def api_toggle_like(song_identifier):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    artist = data.get('artist')
    cover_url = data.get('cover_url')
    duration = data.get('duration')

    song = get_or_create_song(song_identifier, title, artist, cover_url, duration)
    if not song:
        return jsonify({'error': 'Song not found'}), 404

    is_liked = False
    if song in current_user.liked_songs:
        current_user.liked_songs.remove(song)
        is_liked = False
    else:
        current_user.liked_songs.append(song)
        is_liked = True
    db.session.commit()
    return jsonify({
        'status': 'success',
        'is_liked': is_liked,
        'song_id': song.id,
        'title': song.title
    })

@app.route('/api/record_play/<song_identifier>', methods=['POST'])
def api_record_play(song_identifier):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    artist = data.get('artist')
    cover_url = data.get('cover_url')
    duration = data.get('duration')

    song = get_or_create_song(song_identifier, title, artist, cover_url, duration)
    if song:
        song.plays_count = (song.plays_count or 0) + 1
        if current_user.is_authenticated:
            rp = RecentlyPlayed(user_id=current_user.id, song_id=song.id)
            db.session.add(rp)
        db.session.commit()
        return jsonify({'status': 'recorded', 'plays_count': song.plays_count})
    return jsonify({'status': 'ok'}), 200

@app.route('/api/playlists', methods=['GET', 'POST'])
@login_required
def api_playlists():
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        if not name:
            return jsonify({'error': 'Playlist name required'}), 400
        p = Playlist(name=name, description=description, user_id=current_user.id)
        db.session.add(p)
        db.session.commit()
        return jsonify(p.to_dict()), 201
    
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([p.to_dict() for p in playlists])

@app.route('/api/playlist/<int:playlist_id>/add/<song_identifier>', methods=['POST'])
@login_required
def api_playlist_add(playlist_id, song_identifier):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    data = request.get_json(silent=True) or {}
    song = get_or_create_song(song_identifier, data.get('title'), data.get('artist'), data.get('cover_url'), data.get('duration'))
    if not song:
        abort(404)

    if song not in playlist.songs:
        playlist.songs.append(song)
        db.session.commit()
    return jsonify({'status': 'added', 'playlist': playlist.to_dict()})

@app.route('/api/playlist/<int:playlist_id>/remove/<song_identifier>', methods=['POST'])
@login_required
def api_playlist_remove(playlist_id, song_identifier):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    song = None
    if str(song_identifier).isdigit():
        song = Song.query.get(int(song_identifier))
    if not song:
        song = Song.query.filter_by(youtube_id=str(song_identifier)).first()
    if song and song in playlist.songs:
        playlist.songs.remove(song)
        db.session.commit()
    return jsonify({'status': 'removed', 'playlist': playlist.to_dict()})

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    lang = request.args.get('language')
    mood = request.args.get('mood')
    
    query = Song.query
    if q:
        query = query.filter(
            (Song.title.ilike(f"%{q}%")) |
            (Song.genre.ilike(f"%{q}%"))
        )
    if lang:
        query = query.filter(Song.language == lang)
    if mood:
        query = query.filter(Song.mood == mood)
        
    songs = query.limit(20).all()
    user_id = current_user.id if current_user.is_authenticated else None
    return jsonify([s.to_dict(user_id) for s in songs])


# ---------- YOUTUBE SEARCH via yt-dlp (metadata only) ----------
def _fmt_secs(sec):
    """Format seconds to M:SS"""
    if not sec:
        return '0:00'
    m = int(sec) // 60
    s = int(sec) % 60
    return f'{m}:{s:02d}'


def _fmt_views(n):
    """Format view count to human readable"""
    if not n:
        return ''
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f}M views'
    if n >= 1_000:
        return f'{n / 1_000:.1f}K views'
    return f'{n} views'


@app.route('/api/yt/search')
def api_yt_search():
    """
    Search YouTube via yt-dlp Python library (metadata only — no audio is downloaded).
    Playback is handled by YouTube's official embedded IFrame player,
    which respects YouTube ads, DRM and all playback restrictions.
    """
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])

    max_results = min(int(request.args.get('limit', 12)), 20)

    if not YT_DLP_AVAILABLE:
        return jsonify({'error': 'yt-dlp Python library is not available on this server.'}), 500

    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{q} music"
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', []) if info else []

            results = []
            user_liked_ids = []
            if current_user.is_authenticated:
                user_liked_ids = [s.youtube_id for s in current_user.liked_songs if s.youtube_id]

            for d in entries:
                if not d:
                    continue
                vid = d.get('id', '')
                if not vid:
                    continue
                thumb = (
                    d.get('thumbnail')
                    or f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
                )
                results.append({
                    'id': vid,
                    'title': d.get('title', 'Untitled'),
                    'artist': (
                        d.get('channel')
                        or d.get('uploader')
                        or d.get('uploader_id')
                        or 'Universal Artist'
                    ),
                    'cover_url': thumb,
                    'stream_url': f'/api/stream/{vid}',
                    'file_url': f'/api/stream/{vid}',
                    'duration': d.get('duration') or 0,
                    'formatted_duration': _fmt_secs(d.get('duration')),
                    'views': _fmt_views(d.get('view_count')),
                    'source': 'stream',
                    'is_liked': vid in user_liked_ids
                })

            return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- ERROR HANDLERS ----------
@app.errorhandler(403)
def error_403(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_500(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

