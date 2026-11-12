# ROMUSIC — MIDNIGHT LUXE × NEON AURORA

Next-generation, luxury music streaming architecture combining the acoustic soul of high-fidelity sound, digital gallery aesthetics, and futuristic neon visual identity.

Designed from first principles. **Zero generic templates. Zero Spotify clones.**

---

## 🌌 Visual Identity: Midnight Luxe × Neon Aurora

- **Midnight Navy Canvas:** `#090B16`
- **Dark Indigo Surfaces:** `#111426` & `#181C33`
- **Electric Violet Accents:** `#9B5CFF`
- **Neon Cyan Highlights:** `#35D6FF`
- **Soft Lavender Gradients:** `#B57EDC`
- **Rose Magenta Sparks:** `#FF357A`
- **Subtle Glassmorphism:** High blur backdrop filters, hairline neon borders, depth shadows
- **Cinematic Typography:** Editorial headlines via *Syne* + *Plus Jakarta Sans*

---

## ⚡ Key Features

1. **Cinematic Hero Experience:**
   - Real-time personalized greeting
   - Oversized featured album presentation with animated ambient glows
   - Floating action triggers with neon luminescence

2. **Rich Regional & Mood Catalog:**
   - **Malayalam Acoustic Exclusives:** *Premam (Malare)*, *Aavesham (Jaada)*, *Manjummel Boys (Kuthanthram)*
   - **Tamil High-Octane Anthems:** *LEO (Badass)*, *Jailer (Hukum)*
   - **Hindi Soul & Sufi:** *Brahmastra (Kesariya)*, *ANIMAL (Arjan Vailly)*
   - **English Synthwave & Cyber:** *The Weeknd (Blinding Lights)*, *Hans Zimmer (Interstellar)*
   - **Engineered Mood Frequencies:** *Midnight Drive*, *Aurora Sanctuary*, *Neon Focus*, *Cyber Chill*

3. **High-Performance Audio Architecture:**
   - HTTP Range Requests (`206 Partial Content`) for instant scrubbing and seeking
   - Multi-format support: **MP3, WAV, OGG, M4A, FLAC**
   - Out-of-the-box generated harmonic stereo wave tracks

4. **Web Audio API Real-Time Visualizer:**
   - Hardware-accelerated canvas frequency bar rendering
   - Dynamic cyan-to-violet gradient with bloom glow

5. **Full-Featured Suite:**
   - User authentication (hashed passphrases, persistent sessions)
   - Liked Songs & Favorites sanctuary
   - Custom Playlist creation & management
   - Real-time Live Search with instantaneous suggestion dropdown
   - Master track upload portal with artwork extraction
   - Admin governance dashboard for catalog & user management

---

## 🌐 100% Free Cloud Hosting on Render (Auto-Deploy on Push)

This project includes `render.yaml` and `Procfile` configured for **Render.com's Free Web Service tier**.

### Step 1: Create a GitHub Repo & Push Code
1. Go to [github.com/new](https://github.com/new) and create a repository named **`romusic`** (Public or Private).
2. Run in terminal or double click `push_to_github.bat`:
   ```bash
   git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/romusic.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Connect Render for Free Hosting
1. Go to [Render.com](https://render.com) and sign up / log in with your GitHub account.
2. Click **New +** → **Web Service**.
3. Select your **`romusic`** repository.
4. Render automatically detects the configuration from `render.yaml`:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt && python seed_data.py`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Instance Type:** Free
5. Click **Create Web Service**. Within 2-3 minutes, your music platform is live on `https://romusic-xxx.onrender.com`!
6. **Automatic Updates:** Every time you push changes to GitHub (`git push` or double-clicking `push_to_github.bat`), Render automatically rebuilds and updates your live site!

---

## 📱 Android APK & Mobile Installation

There are **two easy ways** to install ROMUSIC on your Android phone:

### Option A: Install Progressive Web App (PWA) — Instant One-Click
1. Open your live hosted site (e.g., `https://romusic.onrender.com`) in **Chrome** or your mobile browser.
2. Tap the **three-dots menu** (⋮) or tap the **"Add ROMUSIC to Home screen" / "Install App"** prompt at the bottom.
3. Tap **Install**. ROMUSIC installs on your phone as a full-screen, standalone app with background playback and its own app icon!

### Option B: Download the Android APK (`ROMUSIC.apk`)
1. In your GitHub repository, click the **Actions** tab.
2. Select the latest workflow run: **Build ROMUSIC APK**.
3. Under **Artifacts**, download **`ROMUSIC-APK`** (or go to **Releases** on GitHub).
4. Transfer or open the `.apk` file on your Android phone and tap **Install**!

---

## 🚀 Instant Launch Instructions

### 1. Requirements
- Python 3.10+ (Tested on Windows with Python 3.14)
- Web Browser (Chrome, Edge, Firefox, Brave, Safari)

### 2. Run the Application
In your terminal, navigate to this project folder:

```powershell
cd "c:\Users\rohit\Downloads\files (1)"
python app.py
```

Or simply double-click **`run.bat`**!

Open your browser at:
👉 **`http://127.0.0.1:5000`**

### 3. Demo Credentials
| Moniker | Passphrase | Role |
|---------|------------|------|
| **rohit** | `password123` | Platform Administrator |
| **aurora_vip** | `password123` | Patron Listener |

*(Or register any new account instantly!)*

---

## 📁 Architecture Directory Layout

```
files (1)/
├── app.py                      # Flask Application Engine & HTTP Range Streaming
├── config.py                   # Configuration & Upload Limits
├── models.py                   # SQLAlchemy Models (User, Artist, Album, Song, Playlist)
├── seed_data.py                # Database population script with rich catalog
├── generate_audio.py           # Harmonic multi-tone stereo audio synthesizer
├── generate_artwork.py         # SVG Luxury Cover Art Generator
├── run.bat                     # Windows one-click start script
├── requirements.txt            # Python dependencies
├── database/                   # SQLite database (romusic.db)
├── music/                      # Master audio tracks
├── static/
│   ├── css/style.css           # Custom Midnight Luxe stylesheet
│   ├── js/
│   │   ├── player.js           # Audio engine & Web Audio visualizer
│   │   └── app.js              # Micro-interactions, toasts, modals & search
│   └── images/
│       ├── romusic_logo.svg    # Official ROMUSIC monogram
│       └── covers/             # High-res SVG album artwork
└── templates/
    ├── base.html               # Main layout, sidebar, bottom nav & persistent player
    ├── index.html              # Home discovery portal & hero
    ├── search.html             # Cinematic search architecture
    ├── library.html            # User sanctuary & playlists
    ├── favorites.html          # Liked tracks
    ├── upload.html             # Audio upload portal
    ├── admin.html              # Governance dashboard
    ├── playlist_detail.html    # Playlist inspection view
    ├── artist_profile.html     # Verified composer discography
    ├── login.html              # Sign in
    ├── register.html           # Sign up
    ├── 403.html                # Access forbidden
    └── 404.html                # Frequency not found
```

---
*Crafted with pure acoustic passion for ROMUSIC.*

