import os
from config import Config
from models import db, User, Artist, Album, Song, Playlist, RecentlyPlayed
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def seed():
    with app.app_context():
        # Ensure database directory exists
        os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
        db.drop_all()
        db.create_all()

        print("Creating users...")
        rohit = User(username='rohit', email='rohit@romusic.io', is_admin=True)
        rohit.set_password('password123')

        listener = User(username='aurora_vip', email='aurora@romusic.io', is_admin=False)
        listener.set_password('password123')

        db.session.add_all([rohit, listener])
        db.session.commit()

        print("Creating artists...")
        artists_data = [
            Artist(
                name='Sushin Shyam',
                bio='Trailblazing composer redefining modern Malayalam cinema soundscapes with electronic fusion, punchy beats, and raw street energy.',
                image_url='/static/images/covers/cover_aavesham.svg',
                monthly_listeners='2.8M',
                is_verified=True
            ),
            Artist(
                name='Anirudh Ravichander',
                bio='India’s biggest musical rockstar, dominating charts with viral electronic anthems, electrifying stadium hooks, and cinematic bass.',
                image_url='/static/images/covers/cover_leo.svg',
                monthly_listeners='7.4M',
                is_verified=True
            ),
            Artist(
                name='Rajesh Murugesan',
                bio='Master of nostalgic acoustic warmth and timeless evergreen melodies that etched Malayalam cinema into world music history.',
                image_url='/static/images/covers/cover_premam.svg',
                monthly_listeners='1.5M',
                is_verified=True
            ),
            Artist(
                name='Pritam',
                bio='The prolific hitmaker of Bollywood, blending Sufi soul, modern acoustic pop, and monumental romantic symphonies.',
                image_url='/static/images/covers/cover_kesariya.svg',
                monthly_listeners='9.1M',
                is_verified=True
            ),
            Artist(
                name='The Weeknd',
                bio='Visionary innovator of futuristic 80s synthwave, midnight dark-pop, and melancholic neon-lit R&B masterpieces.',
                image_url='/static/images/covers/cover_blinding.svg',
                monthly_listeners='18.5M',
                is_verified=True
            ),
            Artist(
                name='Hans Zimmer',
                bio='Legendary acoustic architect creating cosmic, earth-shaking cinematic landscapes and transcendent synth-orchestral journeys.',
                image_url='/static/images/covers/cover_interstellar.svg',
                monthly_listeners='6.2M',
                is_verified=True
            )
        ]
        db.session.add_all(artists_data)
        db.session.commit()

        print("Creating albums...")
        albums_data = [
            Album(title='Premam (Original Motion Picture Soundtrack)', cover_url='/static/images/covers/cover_premam.svg', release_year=2015, genre='Romantic Melodies', language='Malayalam', artist_id=artists_data[2].id),
            Album(title='Aavesham (The Sonic Riot)', cover_url='/static/images/covers/cover_aavesham.svg', release_year=2024, genre='Electronic / Trap', language='Malayalam', artist_id=artists_data[0].id),
            Album(title='Manjummel Boys (Resilience OST)', cover_url='/static/images/covers/cover_manjummel.svg', release_year=2024, genre='Atmospheric Hip-Hop', language='Malayalam', artist_id=artists_data[0].id),
            Album(title='LEO: Bloody Sweet Soundtrack', cover_url='/static/images/covers/cover_leo.svg', release_year=2023, genre='Cyber Metal / Trap', language='Tamil', artist_id=artists_data[1].id),
            Album(title='Jailer (Massive Resonance)', cover_url='/static/images/covers/cover_jailer.svg', release_year=2023, genre='Heroic Bass', language='Tamil', artist_id=artists_data[1].id),
            Album(title='ANIMAL (High Octane)', cover_url='/static/images/covers/cover_animal.svg', release_year=2023, genre='Folk Rock / Electro', language='Hindi', artist_id=artists_data[3].id),
            Album(title='Brahmastra: Part One - Shiva', cover_url='/static/images/covers/cover_kesariya.svg', release_year=2022, genre='Sufi Romantic', language='Hindi', artist_id=artists_data[3].id),
            Album(title='After Hours (Deluxe Aurora Edition)', cover_url='/static/images/covers/cover_blinding.svg', release_year=2020, genre='Synthwave / Pop', language='English', artist_id=artists_data[4].id),
            Album(title='Interstellar: Cosmic Soundscapes', cover_url='/static/images/covers/cover_interstellar.svg', release_year=2014, genre='Cinematic / Ambient', language='English', artist_id=artists_data[5].id),
            Album(title='Midnight Aurora: ROMUSIC Exclusives', cover_url='/static/images/covers/cover_midnight.svg', release_year=2026, genre='Neon Cyberpunk', language='English', artist_id=artists_data[4].id)
        ]
        db.session.add_all(albums_data)
        db.session.commit()

        print("Creating songs...")
        music_base = os.path.join(app.root_path, 'music')
        songs_data = [
            Song(
                title='Malare (Premam)',
                youtube_id='0G2VxhV_gXM',
                cover_url='https://img.youtube.com/vi/0G2VxhV_gXM/hqdefault.jpg',
                duration=314,
                plays_count=184200,
                genre='Romantic Melodies',
                language='Malayalam',
                mood='Aurora',
                lyrics="Malare ninne kaanathirunnal Mizhikal niranjozhukukayayi...",
                artist_id=artists_data[2].id,
                album_id=albums_data[0].id
            ),
            Song(
                title='Jaada (Aavesham)',
                youtube_id='HUAAYwtusLI',
                cover_url='https://img.youtube.com/vi/HUAAYwtusLI/hqdefault.jpg',
                duration=215,
                plays_count=295000,
                genre='Electronic / Trap',
                language='Malayalam',
                mood='Neon Focus',
                lyrics="Ranga annan vannaal pinne aattavum paattavum maari marinjidum!",
                artist_id=artists_data[0].id,
                album_id=albums_data[1].id
            ),
            Song(
                title='Illuminati (Aavesham)',
                youtube_id='tOM-nWPcR4U',
                cover_url='https://img.youtube.com/vi/tOM-nWPcR4U/hqdefault.jpg',
                duration=198,
                plays_count=450000,
                genre='Electronic / Rap',
                language='Malayalam',
                mood='Neon Focus',
                lyrics="Illuminati gunda rap, Bengaluru club anthem...",
                artist_id=artists_data[0].id,
                album_id=albums_data[1].id
            ),
            Song(
                title='Kuthanthram (Manjummel Boys)',
                youtube_id='W6-O00alJUo',
                cover_url='https://img.youtube.com/vi/W6-O00alJUo/hqdefault.jpg',
                duration=174,
                plays_count=210300,
                genre='Atmospheric Hip-Hop',
                language='Malayalam',
                mood='Cyber Chill',
                lyrics="Gunda gunda vegam paarum, manjummel pilleru thakarthu vaarum...",
                artist_id=artists_data[0].id,
                album_id=albums_data[2].id
            ),
            Song(
                title='Badass (LEO)',
                youtube_id='ZdMZ40GSVmc',
                cover_url='https://img.youtube.com/vi/ZdMZ40GSVmc/hqdefault.jpg',
                duration=230,
                plays_count=340100,
                genre='Cyber Metal / Trap',
                language='Tamil',
                mood='Midnight Drive',
                lyrics="Badass Mr Leo Das is a badass! Bloody sweet, never retreat!",
                artist_id=artists_data[1].id,
                album_id=albums_data[3].id
            ),
            Song(
                title='Hukum (Jailer)',
                youtube_id='gB2zKZxESTg',
                cover_url='https://img.youtube.com/vi/gB2zKZxESTg/hqdefault.jpg',
                duration=207,
                plays_count=412000,
                genre='Heroic Bass',
                language='Tamil',
                mood='Euphoria',
                lyrics="Alappara kelapparom... Tiger Ka Hukum!",
                artist_id=artists_data[1].id,
                album_id=albums_data[4].id
            ),
            Song(
                title='Aasa Kooda',
                youtube_id='a3Ue-LN5B9U',
                cover_url='https://img.youtube.com/vi/a3Ue-LN5B9U/hqdefault.jpg',
                duration=220,
                plays_count=380000,
                genre='Indie Pop',
                language='Tamil',
                mood='Aurora',
                lyrics="Aasa kooda enna aachi, nenjukkulle kaadhal poochi...",
                artist_id=artists_data[1].id,
                album_id=albums_data[4].id
            ),
            Song(
                title='Arjan Vailly (ANIMAL)',
                youtube_id='zqGW6x_5N0k',
                cover_url='https://img.youtube.com/vi/zqGW6x_5N0k/hqdefault.jpg',
                duration=182,
                plays_count=528000,
                genre='Folk Rock / Electro',
                language='Hindi',
                mood='Midnight Drive',
                lyrics="Arjan Vailly ne per pair dharke khadke gandasi...",
                artist_id=artists_data[3].id,
                album_id=albums_data[5].id
            ),
            Song(
                title='Kesariya (Brahmastra)',
                youtube_id='BddP6PYo2gs',
                cover_url='https://img.youtube.com/vi/BddP6PYo2gs/hqdefault.jpg',
                duration=268,
                plays_count=615000,
                genre='Sufi Romantic',
                language='Hindi',
                mood='Aurora',
                lyrics="Kesariya tera ishq hai piya, rang jaaun jo main haath lagaun...",
                artist_id=artists_data[3].id,
                album_id=albums_data[6].id
            ),
            Song(
                title='Blinding Lights',
                youtube_id='4NRXx6U8ABQ',
                cover_url='https://img.youtube.com/vi/4NRXx6U8ABQ/hqdefault.jpg',
                duration=260,
                plays_count=892000,
                genre='Synthwave / Pop',
                language='English',
                mood='Cyber Chill',
                lyrics="I said, ooh, I'm blinded by the lights, no I can't sleep until I feel your touch...",
                artist_id=artists_data[4].id,
                album_id=albums_data[7].id
            ),
            Song(
                title='Interstellar Main Theme',
                youtube_id='UDVtMYqUAyw',
                cover_url='https://img.youtube.com/vi/UDVtMYqUAyw/hqdefault.jpg',
                duration=250,
                plays_count=430000,
                genre='Cinematic / Ambient',
                language='English',
                mood='Aurora',
                lyrics="[Instrumental Cosmic Horizon - Organ and Sub-bass waves]",
                artist_id=artists_data[5].id,
                album_id=albums_data[8].id
            ),
            Song(
                title='Midnight Synthwave Chill',
                youtube_id='4xDzrJKXOOY',
                cover_url='https://img.youtube.com/vi/4xDzrJKXOOY/hqdefault.jpg',
                duration=218,
                plays_count=192000,
                genre='Neon Cyberpunk',
                language='English',
                mood='Midnight Drive',
                lyrics="Neon reflections on wet asphalt at 3 AM... Drive into infinity.",
                artist_id=artists_data[4].id,
                album_id=albums_data[9].id
            )
        ]
        db.session.add_all(songs_data)
        db.session.commit()

        # Seed Rohit's liked songs
        rohit.liked_songs.extend([songs_data[0], songs_data[1], songs_data[3], songs_data[6], songs_data[7]])

        # Create playlists
        p1 = Playlist(
            name='God’s Own Cyberpunk (Malayalam)',
            description='The freshest electronic bangers and soulful melodies straight from Kerala.',
            cover_url='/static/images/covers/cover_aavesham.svg',
            user_id=rohit.id
        )
        p1.songs.extend([songs_data[1], songs_data[0], songs_data[2]])

        p2 = Playlist(
            name='Neon Midnight Drive',
            description='Deep sub-bass, 80s analog synth waves, and cinematic rush for late night drives.',
            cover_url='/static/images/covers/cover_midnight.svg',
            user_id=rohit.id
        )
        p2.songs.extend([songs_data[3], songs_data[5], songs_data[7], songs_data[9]])

        p3 = Playlist(
            name='Aurora Chill & Focus',
            description='Binaural acoustic textures and soothing vocal waves for deep immersion.',
            cover_url='/static/images/covers/cover_interstellar.svg',
            user_id=rohit.id
        )
        p3.songs.extend([songs_data[8], songs_data[6], songs_data[0]])

        db.session.add_all([p1, p2, p3])

        # Add recent plays
        rp1 = RecentlyPlayed(user_id=rohit.id, song_id=songs_data[1].id)
        rp2 = RecentlyPlayed(user_id=rohit.id, song_id=songs_data[0].id)
        rp3 = RecentlyPlayed(user_id=rohit.id, song_id=songs_data[7].id)
        db.session.add_all([rp1, rp2, rp3])

        db.session.commit()
        print("Database successfully seeded with luxury music catalog!")

if __name__ == '__main__':
    seed()

