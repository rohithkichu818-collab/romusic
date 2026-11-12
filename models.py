from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association tables
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('liked_at', db.DateTime, default=datetime.utcnow)
)

playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('position', db.Integer, default=0),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar_color = db.Column(db.String(50), default='from-[#9B5CFF] to-[#35D6FF]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    liked_songs = db.relationship('Song', secondary=likes, backref=db.backref('liked_by_users', lazy='dynamic'))
    playlists = db.relationship('Playlist', backref='owner', cascade='all, delete-orphan', lazy=True)
    recent_plays = db.relationship('RecentlyPlayed', backref='user', cascade='all, delete-orphan', lazy=True, order_by='RecentlyPlayed.played_at.desc()')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    monthly_listeners = db.Column(db.String(50), default='1.2M')
    is_verified = db.Column(db.Boolean, default=True)

    albums = db.relationship('Album', backref='artist', cascade='all, delete-orphan', lazy=True)
    songs = db.relationship('Song', backref='artist', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'image_url': self.image_url,
            'monthly_listeners': self.monthly_listeners,
            'is_verified': self.is_verified,
            'song_count': len(self.songs),
            'album_count': len(self.albums)
        }


class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(255))
    release_year = db.Column(db.Integer, default=2024)
    genre = db.Column(db.String(80), default='Electronic')
    language = db.Column(db.String(50), default='English')
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'), nullable=False)

    songs = db.relationship('Song', backref='album', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'cover_url': self.cover_url,
            'release_year': self.release_year,
            'genre': self.genre,
            'language': self.language,
            'artist': self.artist.name if self.artist else 'Unknown Artist',
            'artist_id': self.artist_id,
            'songs': [s.to_dict() for s in self.songs]
        }


class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=True)
    youtube_id = db.Column(db.String(100), nullable=True, index=True)
    cover_url = db.Column(db.String(255))
    duration = db.Column(db.Integer, default=180)  # seconds
    plays_count = db.Column(db.Integer, default=0)
    genre = db.Column(db.String(80), default='Electronic')
    language = db.Column(db.String(50), default='English', index=True) # Malayalam, Tamil, Hindi, English
    mood = db.Column(db.String(50), default='Chill') # Midnight Drive, Neon Focus, Cyber Chill, Euphoria
    lyrics = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    album_id = db.Column(db.Integer, db.ForeignKey('albums.id', ondelete='SET NULL'), nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='SET NULL'), nullable=True)

    def formatted_duration(self):
        mins = self.duration // 60
        secs = self.duration % 60
        return f"{mins}:{secs:02d}"

    def to_dict(self, current_user_id=None):
        is_liked = False
        if current_user_id and current_user_id in [u.id for u in self.liked_by_users]:
            is_liked = True
        stream_id = self.youtube_id if self.youtube_id else str(self.id)
        return {
            'id': stream_id,
            'db_id': self.id,
            'youtube_id': self.youtube_id,
            'title': self.title,
            'artist': self.artist.name if self.artist else 'ROMUSIC Exclusive',
            'artist_id': self.artist_id,
            'album': self.album.title if self.album else 'Single',
            'album_id': self.album_id,
            'cover_url': self.cover_url or '/static/images/default_cover.svg',
            'stream_url': f"/api/stream/{stream_id}",
            'file_url': f"/api/stream/{stream_id}",
            'source': 'stream',
            'duration': self.duration,
            'formatted_duration': self.formatted_duration(),
            'plays_count': self.plays_count,
            'genre': self.genre,
            'language': self.language,
            'mood': self.mood,
            'is_liked': is_liked,
            'lyrics': self.lyrics or ''
        }


class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), default='')
    cover_url = db.Column(db.String(255), default='/static/images/default_cover.svg')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    songs = db.relationship('Song', secondary=playlist_songs, backref=db.backref('in_playlists', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover_url': self.cover_url,
            'song_count': len(self.songs),
            'songs': [s.to_dict() for s in self.songs]
        }


class RecentlyPlayed(db.Model):
    __tablename__ = 'recently_played'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id', ondelete='CASCADE'), nullable=False)
    played_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    song = db.relationship('Song')

