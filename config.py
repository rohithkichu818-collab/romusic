import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'romusic-midnight-luxe-secret-key-2026')
    db_path = BASE_DIR / 'database' / 'romusic.db'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{db_path}")
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / 'music'
    ARTWORK_FOLDER = BASE_DIR / 'static' / 'images' / 'covers'
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}
    MAX_CONTENT_LENGTH = 150 * 1024 * 1024  # 150 MB max upload

