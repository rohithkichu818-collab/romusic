/* ========================================================
   ROMUSIC — ULTIMATE AUDIO STREAMING ENGINE (OPENBLAST-GRADE)
   High-performance pure audio streaming, LRCLIB synced karaoke lyrics,
   real-time neon audio visualizer, sleep timer, dynamic queue & ambient glow.
   ======================================================== */

class RoMusicPlayer {
    constructor() {
        this.audio = new Audio();
        this.audio.preload = 'auto';
        this.queue = [];
        this.currentIndex = -1;
        this.currentTrack = null;
        this.isPlaying = false;
        this.isShuffled = false;
        this.repeatMode = 'all'; // 'off' | 'all' | 'one'
        
        // Lyrics
        this.syncedLyrics = []; // [{ time: float_seconds, text: string }]
        this.activeLyricIndex = -1;
        this.lyricsLoaded = false;
        
        // Sleep Timer
        this.sleepTimerId = null;
        this.sleepTimerRemaining = 0; // seconds
        this.sleepAtTrackEnd = false;
        
        // Active View Tab in Modal: 'art' | 'lyrics' | 'queue'
        this.currentTab = 'art';

        // Web Audio API Visualizer
        this.audioCtx = null;
        this.analyser = null;
        this.sourceNode = null;
        this.visualizerCanvas = null;
        this.canvasCtx = null;
        this.animFrameId = null;
        this.isVisualizerInit = false;

        // Dual Audio Engine: 'html5' (local uploads) | 'youtube' (instant global stream)
        this.currentAudioSource = 'html5';
        this.ytPlayer = null;
        this.ytReady = false;
        this.ytPollTimer = null;

        this.initElements();
        this.bindEvents();
        this.restoreSettings();
        this.initYouTubeEngine();
        this.loadInitialQueue();
    }

    initYouTubeEngine() {
        if (window.YT && window.YT.Player) {
            this.createYTPlayer();
        } else {
            const prevReady = window.onYouTubeIframeAPIReady;
            window.onYouTubeIframeAPIReady = () => {
                if (typeof prevReady === 'function') {
                    try { prevReady(); } catch (e) {}
                }
                this.createYTPlayer();
            };
        }
    }

    createYTPlayer() {
        const container = document.getElementById('romusic-yt-player');
        if (!container || this.ytPlayer) return;

        try {
            this.ytPlayer = new YT.Player('romusic-yt-player', {
                height: '1',
                width: '1',
                playerVars: {
                    'autoplay': 1,
                    'controls': 0,
                    'disablekb': 1,
                    'fs': 0,
                    'playsinline': 1,
                    'rel': 0,
                    'origin': window.location.origin
                },
                events: {
                    'onReady': () => {
                        this.ytReady = true;
                    },
                    'onStateChange': (e) => this.onYTStateChange(e),
                    'onError': (e) => this.onYTError(e)
                }
            });
        } catch (e) {
            console.warn('[RoMusic YT Engine Init]:', e);
        }
    }

    onYTStateChange(event) {
        if (!window.YT) return;
        if (event.data === YT.PlayerState.PLAYING) {
            this.onPlayState(true);
            this.startVisualizer();
            this.startYTPolling();
        } else if (event.data === YT.PlayerState.PAUSED) {
            this.onPlayState(false);
            this.stopYTPolling();
        } else if (event.data === YT.PlayerState.ENDED) {
            this.stopYTPolling();
            this.onEnded();
        } else if (event.data === YT.PlayerState.CUED) {
            if (this.ytPlayer && typeof this.ytPlayer.playVideo === 'function') {
                this.ytPlayer.playVideo();
            }
        }
    }

    onYTError(event) {
        console.warn('[RoMusic YT Engine Error, fallback to direct stream]:', event.data);
        if (this.currentTrack) {
            this.currentAudioSource = 'html5';
            this.stopYTPolling();
            const streamId = this.currentTrack.youtube_id || this.currentTrack.id;
            const tParam = encodeURIComponent(this.currentTrack.title || '');
            const aParam = encodeURIComponent(this.currentTrack.artist || '');
            this.audio.src = `/api/stream/${streamId}?title=${tParam}&artist=${aParam}`;
            this.audio.play().then(() => this.onPlayState(true)).catch(console.warn);
        }
    }

    startYTPolling() {
        this.stopYTPolling();
        this.ytPollTimer = setInterval(() => {
            if (!this.ytPlayer || !this.ytReady || this.currentAudioSource !== 'youtube') return;
            const cur = (typeof this.ytPlayer.getCurrentTime === 'function') ? this.ytPlayer.getCurrentTime() : 0;
            const dur = (typeof this.ytPlayer.getDuration === 'function') ? this.ytPlayer.getDuration() : (this.currentTrack ? this.currentTrack.duration : 0);
            this.onTimeUpdate(cur, dur);
        }, 250);
    }

    stopYTPolling() {
        if (this.ytPollTimer) {
            clearInterval(this.ytPollTimer);
            this.ytPollTimer = null;
        }
    }

    initElements() {
        // Floating Player Bar
        this.floatingPlayer = document.getElementById('floating-player');
        this.thumb = document.getElementById('player-thumb');
        this.title = document.getElementById('player-title');
        this.artist = document.getElementById('player-artist');
        this.qualityTag = document.getElementById('player-quality-tag');
        this.btnPlay = document.getElementById('btn-play');
        this.iconPlay = document.getElementById('icon-play');
        this.btnPrev = document.getElementById('btn-prev');
        this.btnNext = document.getElementById('btn-next');
        this.btnShuffle = document.getElementById('btn-shuffle');
        this.btnRepeat = document.getElementById('btn-repeat');
        this.btnLike = document.getElementById('btn-like');
        this.iconLike = document.getElementById('icon-like');
        this.btnExpand = document.getElementById('btn-expand');
        this.btnLyricsToggle = document.getElementById('btn-toggle-lyrics');
        this.btnSleepTimer = document.getElementById('btn-sleep-timer');
        this.sleepBadge = document.getElementById('sleep-timer-badge');
        this.progressBar = document.getElementById('player-progress');
        this.currentTimeEl = document.getElementById('player-current-time');
        this.durationTimeEl = document.getElementById('player-duration-time');
        this.volumeBar = document.getElementById('player-volume');
        this.btnMute = document.getElementById('btn-mute');
        this.iconVolume = document.getElementById('icon-volume');

        // Fullscreen Modal
        this.modal = document.getElementById('now-playing-modal');
        this.btnCloseModal = document.getElementById('btn-close-modal');
        this.modalCover = document.getElementById('modal-cover');
        this.modalTitle = document.getElementById('modal-title');
        this.modalArtist = document.getElementById('modal-artist');
        this.modalAlbum = document.getElementById('modal-album');
        this.modalGenre = document.getElementById('modal-genre');
        this.modalBtnPlay = document.getElementById('modal-btn-play');
        this.modalIconPlay = document.getElementById('modal-icon-play');
        this.modalBtnPrev = document.getElementById('modal-btn-prev');
        this.modalBtnNext = document.getElementById('modal-btn-next');
        this.modalBtnLike = document.getElementById('modal-btn-like');
        this.modalIconLike = document.getElementById('modal-icon-like');
        this.modalProgress = document.getElementById('modal-progress');
        this.modalCurrentTime = document.getElementById('modal-current-time');
        this.modalDuration = document.getElementById('modal-duration');
        this.queueListEl = document.getElementById('modal-queue-list');
        
        // Lyrics Container
        this.lyricsContainer = document.getElementById('synced-lyrics-container');
        this.lyricsList = document.getElementById('synced-lyrics-list');
        this.plainLyrics = document.getElementById('modal-lyrics');

        // Visualizer Canvas
        this.visualizerCanvas = document.getElementById('audio-visualizer');
        if (this.visualizerCanvas) {
            this.canvasCtx = this.visualizerCanvas.getContext('2d');
        }

        // Sleep Timer Modal
        this.sleepTimerModal = document.getElementById('sleep-timer-modal');
    }

    bindEvents() {
        // Playback buttons
        if (this.btnPlay) this.btnPlay.addEventListener('click', () => this.togglePlay());
        if (this.btnPrev) this.btnPrev.addEventListener('click', () => this.playPrevious());
        if (this.btnNext) this.btnNext.addEventListener('click', () => this.playNext());
        if (this.btnShuffle) this.btnShuffle.addEventListener('click', () => this.toggleShuffle());
        if (this.btnRepeat) this.btnRepeat.addEventListener('click', () => this.toggleRepeat());
        if (this.btnLike) this.btnLike.addEventListener('click', () => this.toggleCurrentLike());
        if (this.btnExpand) this.btnExpand.addEventListener('click', () => this.openModal('art'));
        if (this.btnLyricsToggle) this.btnLyricsToggle.addEventListener('click', () => this.openModal('lyrics'));
        if (this.btnSleepTimer) this.btnSleepTimer.addEventListener('click', () => this.toggleSleepTimerModal());

        // Modal buttons
        if (this.btnCloseModal) this.btnCloseModal.addEventListener('click', () => this.closeModal());
        if (this.modalBtnPlay) this.modalBtnPlay.addEventListener('click', () => this.togglePlay());
        if (this.modalBtnPrev) this.modalBtnPrev.addEventListener('click', () => this.playPrevious());
        if (this.modalBtnNext) this.modalBtnNext.addEventListener('click', () => this.playNext());
        if (this.modalBtnLike) this.modalBtnLike.addEventListener('click', () => this.toggleCurrentLike());

        // Seek bars
        if (this.progressBar) {
            this.progressBar.addEventListener('input', (e) => this.seek(e.target.value));
        }
        if (this.modalProgress) {
            this.modalProgress.addEventListener('input', (e) => this.seek(e.target.value));
        }

        // Volume controls
        if (this.volumeBar) {
            this.volumeBar.addEventListener('input', (e) => this.setVolume(e.target.value));
        }
        if (this.btnMute) {
            this.btnMute.addEventListener('click', () => this.toggleMute());
        }

        // HTML5 Audio Events
        this.audio.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.audio.addEventListener('loadedmetadata', () => this.onLoadedMetadata());
        this.audio.addEventListener('ended', () => this.onEnded());
        this.audio.addEventListener('play', () => this.onPlayState(true));
        this.audio.addEventListener('pause', () => this.onPlayState(false));
        this.audio.addEventListener('error', (e) => this.onError(e));

        // Global shortcuts
        window.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.code === 'Space') {
                e.preventDefault();
                this.togglePlay();
            } else if (e.code === 'ArrowRight') {
                this.seekRelative(5);
            } else if (e.code === 'ArrowLeft') {
                this.seekRelative(-5);
            } else if (e.key === 'm' || e.key === 'M') {
                this.toggleMute();
            } else if (e.key === 'l' || e.key === 'L') {
                this.openModal('lyrics');
            }
        });

        // Window resize for visualizer canvas
        window.addEventListener('resize', () => {
            if (this.visualizerCanvas) {
                this.visualizerCanvas.width = this.visualizerCanvas.offsetWidth;
                this.visualizerCanvas.height = this.visualizerCanvas.offsetHeight;
            }
        });
    }

    restoreSettings() {
        const savedVol = localStorage.getItem('romusic_volume');
        if (savedVol !== null) {
            this.setVolume(parseFloat(savedVol));
            if (this.volumeBar) this.volumeBar.value = savedVol;
        } else {
            this.setVolume(85);
        }

        const savedRepeat = localStorage.getItem('romusic_repeat');
        if (savedRepeat) {
            this.repeatMode = savedRepeat;
            this.updateRepeatUI();
        }
    }

    /* ------- AUDIO ENGINE & PLAYBACK ------- */
    async playTrack(track, queueList = null) {
        if (!track) return;

        // Init Web Audio API on first user interaction
        this.ensureAudioContext();

        if (queueList && Array.isArray(queueList) && queueList.length > 0) {
            this.queue = [...queueList];
            this.currentIndex = this.queue.findIndex(t => String(t.id) === String(track.id));
            if (this.currentIndex === -1) {
                this.queue.unshift(track);
                this.currentIndex = 0;
            }
        } else {
            // Fresh song chosen by user: Initialize dynamic Spotify Radio queue based on this track!
            this.queue = [track];
            this.currentIndex = 0;
        }

        this.currentTrack = track;
        this._retryCount = 0;
        this.updateMetadataUI(track);
        this.renderQueue();

        // Persist active track & queue so navigation never loses it
        try {
            localStorage.setItem('romusic_current_track', JSON.stringify(track));
            localStorage.setItem('romusic_queue', JSON.stringify(this.queue));
            localStorage.setItem('romusic_current_index', this.currentIndex);
        } catch (e) {}

        // Fetch Spotify-grade Smart Recommendations for the current track!
        this.fetchSmartRecommendations(track);

        // Determine stream ID
        const streamId = track.youtube_id || (isNaN(track.id) ? track.id : null);

        // Check if we can play directly via high-speed global delivery engine (YouTube IFrame API)
        if (streamId && (this.ytReady || (window.YT && window.YT.Player))) {
            this.currentAudioSource = 'youtube';
            this.audio.pause();
            
            if (this.ytPlayer && typeof this.ytPlayer.loadVideoById === 'function') {
                this.ytPlayer.loadVideoById(streamId);
                this.ytPlayer.playVideo();
                this.onPlayState(true);
            } else {
                this.createYTPlayer();
                setTimeout(() => {
                    if (this.ytPlayer && typeof this.ytPlayer.loadVideoById === 'function') {
                        this.ytPlayer.loadVideoById(streamId);
                        this.ytPlayer.playVideo();
                        this.onPlayState(true);
                    }
                }, 600);
            }
        } else {
            // HTML5 Fallback or local file
            this.currentAudioSource = 'html5';
            this.stopYTPolling();
            if (this.ytPlayer && typeof this.ytPlayer.stopVideo === 'function') {
                this.ytPlayer.stopVideo();
            }

            const sId = track.youtube_id || track.id;
            const tParam = encodeURIComponent(track.title || '');
            const aParam = encodeURIComponent(track.artist || '');
            const streamUrl = `/api/stream/${sId}?title=${tParam}&artist=${aParam}`;

            this.audio.src = streamUrl;
            
            try {
                await this.audio.play();
                this.onPlayState(true);
            } catch (err) {
                console.warn('[RoMusic Playback Error]:', err);
            }
        }

        // Fetch LRCLIB synchronized lyrics
        this.fetchLyrics(track.title, track.artist);

        // Record play count on backend
        this.recordPlay(track);

        // Start dynamic visualizer
        this.startVisualizer();
    }

    togglePlay() {
        if (!this.currentTrack) {
            if (this.queue.length > 0) {
                this.playTrack(this.queue[0]);
            }
            return;
        }

        this.ensureAudioContext();

        if (this.currentAudioSource === 'youtube' && this.ytPlayer) {
            if (this.isPlaying) {
                if (typeof this.ytPlayer.pauseVideo === 'function') this.ytPlayer.pauseVideo();
                this.onPlayState(false);
            } else {
                if (typeof this.ytPlayer.playVideo === 'function') this.ytPlayer.playVideo();
                this.onPlayState(true);
            }
            return;
        }

        if (this.audio.paused) {
            this.audio.play().then(() => this.onPlayState(true)).catch(console.warn);
        } else {
            this.audio.pause();
            this.onPlayState(false);
        }
    }

    playNext() {
        if (this.queue.length === 0) return;
        if (this.isShuffled) {
            this.currentIndex = Math.floor(Math.random() * this.queue.length);
        } else {
            this.currentIndex = (this.currentIndex + 1) % this.queue.length;
        }
        const nextTrack = this.queue[this.currentIndex];
        this.playTrack(nextTrack, this.queue);

        // Spotify-style endless stream: fetch more related tracks when nearing end of queue
        if (this.currentIndex >= this.queue.length - 2) {
            this.fetchSmartRecommendations(nextTrack);
        }
    }

    playPrevious() {
        if (this.queue.length === 0) return;
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            return;
        }
        this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
        this.playTrack(this.queue[this.currentIndex], this.queue);
    }

    async fetchSmartRecommendations(track) {
        if (!track || !track.title) return;
        try {
            const title = encodeURIComponent(track.title || '');
            const artist = encodeURIComponent(track.artist || '');
            const genre = encodeURIComponent(track.genre || '');
            const lang = encodeURIComponent(track.language || '');
            const res = await fetch(`/api/recommendations?title=${title}&artist=${artist}&genre=${genre}&language=${lang}`);
            if (!res.ok) return;
            const recs = await res.json();
            if (Array.isArray(recs) && recs.length > 0) {
                // Deduplicate against existing tracks in the queue
                const existingIds = new Set(this.queue.map(t => String(t.youtube_id || t.id)));
                const newTracks = recs.filter(t => !existingIds.has(String(t.youtube_id || t.id)));

                if (newTracks.length > 0) {
                    this.queue = [...this.queue, ...newTracks];
                    this.renderQueue();
                    try {
                        localStorage.setItem('romusic_queue', JSON.stringify(this.queue));
                    } catch (e) {}
                }
            }
        } catch (e) {
            console.warn('[Smart Recommendations Error]:', e);
        }
    }

    seek(percent) {
        if (this.currentAudioSource === 'youtube' && this.ytPlayer) {
            const dur = (typeof this.ytPlayer.getDuration === 'function' ? this.ytPlayer.getDuration() : 0) || (this.currentTrack ? this.currentTrack.duration : 0);
            if (dur > 0) {
                const targetTime = (percent / 100) * dur;
                if (typeof this.ytPlayer.seekTo === 'function') this.ytPlayer.seekTo(targetTime, true);
                this.onTimeUpdate(targetTime, dur);
            }
            return;
        }

        if (!this.audio.duration || isNaN(this.audio.duration)) return;
        const targetTime = (percent / 100) * this.audio.duration;
        this.audio.currentTime = targetTime;
    }

    seekToTime(seconds) {
        if (this.currentAudioSource === 'youtube' && this.ytPlayer) {
            if (typeof this.ytPlayer.seekTo === 'function') {
                this.ytPlayer.seekTo(seconds, true);
                this.onTimeUpdate(seconds);
            }
            return;
        }

        if (seconds >= 0 && this.audio.duration && seconds <= this.audio.duration) {
            this.audio.currentTime = seconds;
            if (this.audio.paused) {
                this.audio.play().catch(console.warn);
            }
        }
    }

    seekRelative(deltaSeconds) {
        if (this.currentAudioSource === 'youtube' && this.ytPlayer) {
            const cur = (typeof this.ytPlayer.getCurrentTime === 'function') ? this.ytPlayer.getCurrentTime() : 0;
            const dur = (typeof this.ytPlayer.getDuration === 'function') ? this.ytPlayer.getDuration() : 0;
            const target = Math.max(0, Math.min(dur || 9999, cur + deltaSeconds));
            if (typeof this.ytPlayer.seekTo === 'function') this.ytPlayer.seekTo(target, true);
            this.onTimeUpdate(target, dur);
            return;
        }

        if (!this.audio.duration) return;
        this.audio.currentTime = Math.max(0, Math.min(this.audio.duration, this.audio.currentTime + deltaSeconds));
    }

    setVolume(value) {
        const vol = Math.max(0, Math.min(100, parseFloat(value)));
        this.audio.volume = vol / 100;
        if (this.ytPlayer && typeof this.ytPlayer.setVolume === 'function') {
            try { this.ytPlayer.setVolume(vol); } catch (e) {}
        }
        localStorage.setItem('romusic_volume', value);
        this.updateVolumeIcon(vol / 100);
    }

    toggleMute() {
        if (this.currentAudioSource === 'youtube' && this.ytPlayer && typeof this.ytPlayer.isMuted === 'function') {
            try {
                if (this.ytPlayer.isMuted()) {
                    this.ytPlayer.unMute();
                    this.updateVolumeIcon(this.audio.volume || 0.85);
                } else {
                    this.ytPlayer.mute();
                    this.updateVolumeIcon(0);
                }
            } catch (e) {}
            return;
        }

        if (this.audio.volume > 0) {
            this._prevVolume = this.audio.volume;
            this.audio.volume = 0;
            if (this.volumeBar) this.volumeBar.value = 0;
            this.updateVolumeIcon(0);
        } else {
            const restore = this._prevVolume || 0.85;
            this.audio.volume = restore;
            if (this.volumeBar) this.volumeBar.value = restore * 100;
            this.updateVolumeIcon(restore);
        }
    }

    updateVolumeIcon(vol) {
        if (!this.iconVolume) return;
        if (vol === 0) {
            this.iconVolume.setAttribute('data-lucide', 'volume-x');
        } else if (vol < 0.5) {
            this.iconVolume.setAttribute('data-lucide', 'volume-1');
        } else {
            this.iconVolume.setAttribute('data-lucide', 'volume-2');
        }
        if (window.lucide) lucide.createIcons();
    }

    toggleShuffle() {
        this.isShuffled = !this.isShuffled;
        if (this.btnShuffle) {
            this.btnShuffle.classList.toggle('text-[#35D6FF]', this.isShuffled);
            this.btnShuffle.classList.toggle('text-gray-400', !this.isShuffled);
        }
        this.showToast(this.isShuffled ? 'Shuffle: Enabled' : 'Shuffle: Sequential');
    }

    toggleRepeat() {
        const modes = ['all', 'one', 'off'];
        const idx = modes.indexOf(this.repeatMode);
        this.repeatMode = modes[(idx + 1) % modes.length];
        localStorage.setItem('romusic_repeat', this.repeatMode);
        this.updateRepeatUI();
        this.showToast(`Repeat: ${this.repeatMode.toUpperCase()}`);
    }

    updateRepeatUI() {
        if (!this.btnRepeat) return;
        this.btnRepeat.classList.remove('text-[#35D6FF]', 'text-gray-400', 'text-[#9B5CFF]');
        if (this.repeatMode === 'all') {
            this.btnRepeat.classList.add('text-[#35D6FF]');
            this.btnRepeat.setAttribute('title', 'Repeat All');
        } else if (this.repeatMode === 'one') {
            this.btnRepeat.classList.add('text-[#9B5CFF]');
            this.btnRepeat.setAttribute('title', 'Repeat Current Track');
        } else {
            this.btnRepeat.classList.add('text-gray-400');
            this.btnRepeat.setAttribute('title', 'Repeat Off');
        }
    }

    /* ------- AUDIO EVENT HANDLERS ------- */
    onTimeUpdate(forcedCurrent = null, forcedDuration = null) {
        const current = forcedCurrent !== null ? forcedCurrent : (this.audio.currentTime || 0);
        const duration = forcedDuration !== null ? forcedDuration : (this.audio.duration || (this.currentTrack ? this.currentTrack.duration : 0));

        if (duration > 0) {
            const percent = (current / duration) * 100;
            if (this.progressBar) this.progressBar.value = percent;
            if (this.modalProgress) this.modalProgress.value = percent;
            const mobileProg = document.getElementById('mobile-mini-progress');
            if (mobileProg) mobileProg.style.width = `${percent}%`;
        }

        const currentFormatted = this.formatTime(current);
        const durationFormatted = this.formatTime(duration);

        if (this.currentTimeEl) this.currentTimeEl.textContent = currentFormatted;
        if (this.modalCurrentTime) this.modalCurrentTime.textContent = currentFormatted;
        if (this.durationTimeEl && duration > 0) this.durationTimeEl.textContent = durationFormatted;
        if (this.modalDuration && duration > 0) this.modalDuration.textContent = durationFormatted;

        // Synchronize LRCLIB karaoke lyrics
        if (this.syncedLyrics && this.syncedLyrics.length > 0) {
            this.syncLyrics(current);
        }
    }

    onLoadedMetadata() {
        const duration = this.audio.duration;
        if (duration && !isNaN(duration)) {
            const formatted = this.formatTime(duration);
            if (this.durationTimeEl) this.durationTimeEl.textContent = formatted;
            if (this.modalDuration) this.modalDuration.textContent = formatted;
        }
    }

    onEnded() {
        if (this.sleepAtTrackEnd) {
            this.setSleepTimer(0);
            this.onPlayState(false);
            this.showToast('Sleep Timer: Playback ended');
            return;
        }

        // Avoid premature skipping: only skip if track actually played close to completion
        const current = this.audio.currentTime || 0;
        const duration = this.audio.duration || 0;
        if (duration > 0 && current < duration - 2.5) {
            console.warn('[RoMusic onEnded Ignored]: Playback ended prematurely.');
            return;
        }

        if (this.repeatMode === 'one') {
            this.audio.currentTime = 0;
            this.audio.play().catch(console.warn);
        } else if (this.repeatMode === 'all' || this.isShuffled) {
            this.playNext();
        } else if (this.currentIndex < this.queue.length - 1) {
            this.playNext();
        } else {
            this.onPlayState(false);
        }
    }

    onPlayState(isPlaying) {
        this.isPlaying = isPlaying;
        
        // Update Bottom Player Play Button directly with clean SVGs
        if (this.btnPlay) {
            this.btnPlay.innerHTML = isPlaying ? `
                <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            ` : `
                <svg class="w-5 h-5 fill-current ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 3 20 12 6 21 6 3"></polygon>
                </svg>
            `;
            this.btnPlay.setAttribute('title', isPlaying ? 'Pause' : 'Play');
        }

        // Update Mobile Play Button
        const btnPlayMobile = document.getElementById('btn-play-mobile');
        if (btnPlayMobile) {
            btnPlayMobile.innerHTML = isPlaying ? `
                <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            ` : `
                <svg class="w-4 h-4 fill-current ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 3 20 12 6 21 6 3"></polygon>
                </svg>
            `;
            btnPlayMobile.setAttribute('title', isPlaying ? 'Pause' : 'Play');
        }

        // Update Modal Play Button directly with clean SVGs
        if (this.modalBtnPlay) {
            this.modalBtnPlay.innerHTML = isPlaying ? `
                <svg class="w-8 h-8 fill-current" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            ` : `
                <svg class="w-8 h-8 fill-current ml-1" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 3 20 12 6 21 6 3"></polygon>
                </svg>
            `;
            this.modalBtnPlay.setAttribute('title', isPlaying ? 'Pause' : 'Play');
        }

        // Update all play buttons on cards across the page
        document.querySelectorAll('[data-action="play-song"]').forEach(el => {
            try {
                const songData = JSON.parse(el.getAttribute('data-song') || '{}');
                const isThisTrack = this.currentTrack && (String(songData.id) === String(this.currentTrack.id) || String(songData.youtube_id) === String(this.currentTrack.id));
                const playIconEl = el.querySelector('.card-play-btn');
                if (playIconEl) {
                    if (isThisTrack && isPlaying) {
                        playIconEl.innerHTML = `
                            <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24" fill="currentColor">
                                <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                                <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                            </svg>
                        `;
                    } else {
                        playIconEl.innerHTML = `
                            <svg class="w-5 h-5 fill-current ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="6 3 20 12 6 21 6 3"></polygon>
                            </svg>
                        `;
                    }
                }
            } catch (e) {}
        });

        // Vinyl Artwork spinning
        if (this.modalCover) {
            if (isPlaying) {
                this.modalCover.classList.add('spinning-vinyl');
                this.modalCover.classList.remove('spinning-vinyl-paused');
            } else {
                this.modalCover.classList.add('spinning-vinyl-paused');
            }
        }
    }

    onError(e) {
        console.warn('[RoMusic Audio Error]:', e);
        this._retryCount = (this._retryCount || 0) + 1;

        // Auto-recover via direct stream engine if available
        if (this.currentTrack && (this.currentTrack.youtube_id || isNaN(this.currentTrack.id))) {
            const vid = this.currentTrack.youtube_id || this.currentTrack.id;
            if (this.ytReady && this.ytPlayer && typeof this.ytPlayer.loadVideoById === 'function') {
                this.currentAudioSource = 'youtube';
                this.ytPlayer.loadVideoById(vid);
                this.ytPlayer.playVideo();
                this.onPlayState(true);
                return;
            }
        }
        
        if (this._retryCount <= 2 && this.currentTrack) {
            this.showToast('Re-connecting audio stream...');
            setTimeout(() => {
                if (!this.currentTrack) return;
                const streamId = this.currentTrack.youtube_id || this.currentTrack.id;
                const tParam = encodeURIComponent(this.currentTrack.title || '');
                const aParam = encodeURIComponent(this.currentTrack.artist || '');
                this.audio.src = `/api/stream/${streamId}?title=${tParam}&artist=${aParam}&ts=${Date.now()}`;
                this.audio.play().then(() => this.onPlayState(true)).catch(console.warn);
            }, 1000);
        } else {
            this.onPlayState(false);
            this.showToast('Audio stream unavailable. Tap play to retry.');
        }
    }

    /* ------- UI UPDATES & METADATA ------- */
    updateMetadataUI(track) {
        if (this.thumb) this.thumb.src = track.cover_url || '/static/images/covers/cover_midnight.svg';
        if (this.title) this.title.textContent = track.title || 'Untitled Track';
        if (this.artist) this.artist.textContent = track.artist || 'ROMUSIC Soundscape';

        if (this.modalCover) this.modalCover.src = track.cover_url || '/static/images/covers/cover_midnight.svg';
        if (this.modalTitle) this.modalTitle.textContent = track.title || 'Untitled Track';
        if (this.modalArtist) this.modalArtist.textContent = track.artist || 'ROMUSIC Artist';
        if (this.modalAlbum) this.modalAlbum.textContent = track.album || 'Single Edition';
        if (this.modalGenre) this.modalGenre.textContent = `${track.language || 'Global'} • ${track.genre || 'Electronic'}`;

        this.updateLikeUI(Boolean(track.is_liked));

        // Update Quality Pill
        if (this.qualityTag) {
            this.qualityTag.innerHTML = `
                <span class="w-1.5 h-1.5 rounded-full bg-[#35D6FF] animate-pulse inline-block mr-1"></span>
                <span>HQ 256K</span>
            `;
        }

        // Update dynamic ambient backdrop glow
        this.updateAmbientGlow(track);
    }

    updateLikeUI(isLiked) {
        const mobileIconLike = document.getElementById('icon-like-mobile');
        [this.iconLike, this.modalIconLike, mobileIconLike].forEach(icon => {
            if (!icon) return;
            if (isLiked) {
                icon.classList.add('fill-rose-500', 'text-rose-500');
                icon.classList.remove('text-gray-400');
            } else {
                icon.classList.remove('fill-rose-500', 'text-rose-500');
                icon.classList.add('text-gray-400');
            }
        });
    }

    async toggleCurrentLike() {
        if (!this.currentTrack) return;
        const track = this.currentTrack;
        const trackId = track.youtube_id || track.id;

        try {
            const resp = await fetch(`/api/like/${trackId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: track.title,
                    artist: track.artist,
                    cover_url: track.cover_url,
                    duration: track.duration
                })
            });

            if (resp.status === 401) {
                this.showToast('Sign in to save favorites');
                return;
            }

            const data = await resp.json();
            if (data.status === 'success') {
                track.is_liked = data.is_liked;
                this.updateLikeUI(data.is_liked);
                this.showToast(data.is_liked ? 'Added to Liked Songs' : 'Removed from Liked Songs');
            }
        } catch (err) {
            console.error('[Like Error]:', err);
        }
    }

    async recordPlay(track) {
        const trackId = track.youtube_id || track.id;
        try {
            await fetch(`/api/record_play/${trackId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: track.title,
                    artist: track.artist,
                    cover_url: track.cover_url,
                    duration: track.duration
                })
            });
        } catch (e) {
            // Ignore analytics error
        }
    }

    /* ------- OPENBLAST LRCLIB SYNCHRONIZED LYRICS ------- */
    async fetchLyrics(title, artist) {
        this.syncedLyrics = [];
        this.activeLyricIndex = -1;
        this.lyricsLoaded = false;

        if (this.lyricsList) {
            this.lyricsList.innerHTML = `
                <div class="flex flex-col items-center justify-center py-20 text-gray-500 space-y-3">
                    <div class="w-6 h-6 border-2 border-[#35D6FF] border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-xs uppercase tracking-wider font-mono">Aligning synced lyrics...</span>
                </div>
            `;
        }

        try {
            const q = `/api/lyrics?title=${encodeURIComponent(title || '')}&artist=${encodeURIComponent(artist || '')}`;
            const res = await fetch(q);
            const data = await res.json();

            if (data.found && data.synced_lyrics) {
                this.parseLrc(data.synced_lyrics);
                this.renderSyncedLyrics();
            } else if (data.found && data.plain_lyrics) {
                this.renderPlainLyrics(data.plain_lyrics);
            } else {
                this.renderNoLyrics();
            }
        } catch (err) {
            console.warn('[Lyrics Fetch Error]:', err);
            this.renderNoLyrics();
        }
    }

    parseLrc(lrcText) {
        const lines = lrcText.split('\n');
        const parsed = [];
        const timeRegex = /\[(\d{2}):(\d{2})\.?(\d{0,3})\]/;

        for (let rawLine of lines) {
            const match = timeRegex.exec(rawLine);
            if (match) {
                const minutes = parseInt(match[1], 10);
                const seconds = parseInt(match[2], 10);
                const ms = match[3] ? parseInt(match[3].padEnd(3, '0').slice(0, 3), 10) : 0;
                const totalSeconds = minutes * 60 + seconds + ms / 1000;
                const text = rawLine.replace(/\[\d{2}:\d{2}\.?\d{0,3}\]/g, '').trim();
                if (text) {
                    parsed.push({ time: totalSeconds, text });
                }
            }
        }

        parsed.sort((a, b) => a.time - b.time);
        this.syncedLyrics = parsed;
        this.lyricsLoaded = parsed.length > 0;
    }

    renderSyncedLyrics() {
        if (!this.lyricsList) return;
        this.lyricsList.innerHTML = '';

        this.syncedLyrics.forEach((line, index) => {
            const el = document.createElement('div');
            el.className = 'lyric-line';
            el.dataset.index = index;
            el.dataset.time = line.time;
            el.textContent = line.text;
            el.onclick = () => this.seekToTime(line.time);
            this.lyricsList.appendChild(el);
        });
    }

    renderPlainLyrics(plainText) {
        if (!this.lyricsList) return;
        this.syncedLyrics = [];
        const paragraphs = plainText.split('\n').filter(l => l.trim().length > 0);
        this.lyricsList.innerHTML = `
            <div class="py-6 px-4 space-y-3 text-center">
                <span class="text-[11px] font-mono text-[#35D6FF] tracking-wider uppercase block mb-4">Official Lyrics</span>
                ${paragraphs.map(p => `<p class="text-base text-gray-300 leading-relaxed">${this.escapeHtml(p)}</p>`).join('')}
            </div>
        `;
    }

    renderNoLyrics() {
        if (!this.lyricsList) return;
        this.syncedLyrics = [];
        this.lyricsList.innerHTML = `
            <div class="flex flex-col items-center justify-center py-20 text-gray-500 space-y-3">
                <i data-lucide="music-4" class="w-8 h-8 text-gray-600"></i>
                <span class="text-sm text-gray-400 font-medium">Instrumental Resonance</span>
                <span class="text-xs text-gray-600">No synchronized lyrics available for this rendition</span>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }

    syncLyrics(currentTime) {
        if (!this.syncedLyrics || this.syncedLyrics.length === 0 || !this.lyricsList) return;

        let activeIdx = -1;
        for (let i = 0; i < this.syncedLyrics.length; i++) {
            if (this.syncedLyrics[i].time <= currentTime + 0.15) {
                activeIdx = i;
            } else {
                break;
            }
        }

        if (activeIdx !== this.activeLyricIndex) {
            this.activeLyricIndex = activeIdx;
            const lineEls = this.lyricsList.querySelectorAll('.lyric-line');
            
            lineEls.forEach((el, idx) => {
                el.classList.remove('active', 'past');
                if (idx === activeIdx) {
                    el.classList.add('active');
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else if (idx < activeIdx) {
                    el.classList.add('past');
                }
            });
        }
    }

    /* ------- SLEEP TIMER (OPENBLAST FEATURE) ------- */
    toggleSleepTimerModal() {
        if (!this.sleepTimerModal) return;
        this.sleepTimerModal.classList.toggle('hidden');
    }

    setSleepTimer(minutes) {
        if (this.sleepTimerId) {
            clearInterval(this.sleepTimerId);
            this.sleepTimerId = null;
        }

        if (minutes === 'end_of_track') {
            this.sleepAtTrackEnd = true;
            this.sleepTimerRemaining = 0;
            if (this.sleepBadge) {
                this.sleepBadge.textContent = 'Track End';
                this.sleepBadge.classList.remove('hidden');
            }
            this.showToast('Sleep Timer set: Stop at track end');
            if (this.sleepTimerModal) this.sleepTimerModal.classList.add('hidden');
            return;
        }

        this.sleepAtTrackEnd = false;
        const mins = parseInt(minutes, 10);
        
        if (!mins || mins <= 0) {
            if (this.sleepBadge) this.sleepBadge.classList.add('hidden');
            this.showToast('Sleep Timer: Disabled');
            if (this.sleepTimerModal) this.sleepTimerModal.classList.add('hidden');
            return;
        }

        this.sleepTimerRemaining = mins * 60;
        if (this.sleepBadge) {
            this.sleepBadge.textContent = `${mins}m`;
            this.sleepBadge.classList.remove('hidden');
        }
        this.showToast(`Sleep Timer set for ${mins} minutes`);
        if (this.sleepTimerModal) this.sleepTimerModal.classList.add('hidden');

        this.sleepTimerId = setInterval(() => {
            this.sleepTimerRemaining--;
            if (this.sleepTimerRemaining <= 0) {
                clearInterval(this.sleepTimerId);
                this.sleepTimerId = null;
                this.fadeOutAndPause();
                if (this.sleepBadge) this.sleepBadge.classList.add('hidden');
                this.showToast('Sleep Timer: Goodnight, audio paused');
            } else if (this.sleepBadge) {
                const remMins = Math.ceil(this.sleepTimerRemaining / 60);
                this.sleepBadge.textContent = `${remMins}m`;
            }
        }, 1000);
    }

    fadeOutAndPause() {
        const initialVol = this.audio.volume;
        const step = initialVol / 20;
        const fadeInterval = setInterval(() => {
            if (this.audio.volume > step) {
                this.audio.volume -= step;
            } else {
                clearInterval(fadeInterval);
                this.audio.pause();
                this.audio.volume = initialVol;
                this.onPlayState(false);
            }
        }, 150);
    }

    /* ------- FULLSCREEN MODAL & VIEW TABS ------- */
    openModal(tab = 'art') {
        if (!this.modal) return;
        this.modal.classList.remove('hidden-modal');
        this.modal.classList.add('visible-modal');
        document.body.style.overflow = 'hidden';
        this.switchTab(tab);
    }

    closeModal() {
        if (!this.modal) return;
        this.modal.classList.remove('visible-modal');
        this.modal.classList.add('hidden-modal');
        document.body.style.overflow = '';
    }

    switchTab(tabName) {
        this.currentTab = tabName;
        const artPane = document.getElementById('modal-pane-art');
        const lyricsPane = document.getElementById('modal-pane-lyrics');
        const queuePane = document.getElementById('modal-pane-queue');

        const tabArtBtn = document.getElementById('tab-btn-art');
        const tabLyricsBtn = document.getElementById('tab-btn-lyrics');
        const tabQueueBtn = document.getElementById('tab-btn-queue');

        [artPane, lyricsPane, queuePane].forEach(p => p && p.classList.add('hidden'));
        [tabArtBtn, tabLyricsBtn, tabQueueBtn].forEach(b => b && b.classList.remove('active'));

        if (tabName === 'art' && artPane) {
            artPane.classList.remove('hidden');
            if (tabArtBtn) tabArtBtn.classList.add('active');
        } else if (tabName === 'lyrics' && lyricsPane) {
            lyricsPane.classList.remove('hidden');
            if (tabLyricsBtn) tabLyricsBtn.classList.add('active');
            if (this.lyricsContainer && this.activeLyricIndex >= 0) {
                const activeEl = this.lyricsList.querySelector('.lyric-line.active');
                if (activeEl) activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else if (tabName === 'queue' && queuePane) {
            queuePane.classList.remove('hidden');
            if (tabQueueBtn) tabQueueBtn.classList.add('active');
            this.renderQueue();
        }
    }

    renderQueue() {
        if (!this.queueListEl) return;
        this.queueListEl.innerHTML = '';

        if (this.queue.length === 0) {
            this.queueListEl.innerHTML = '<div class="text-xs text-gray-500 py-4 text-center">Queue is empty</div>';
            return;
        }

        this.queue.forEach((track, idx) => {
            const isCurrent = idx === this.currentIndex;
            const el = document.createElement('div');
            el.className = `flex items-center space-x-3 p-2.5 rounded-xl cursor-pointer transition ${isCurrent ? 'bg-[#9B5CFF]/20 border border-[#35D6FF]/40 text-white' : 'hover:bg-white/5 text-gray-300'}`;
            el.innerHTML = `
                <div class="relative w-9 h-9 rounded-lg overflow-hidden flex-shrink-0">
                    <img src="${track.cover_url || '/static/images/covers/cover_midnight.svg'}" class="w-full h-full object-cover">
                    ${isCurrent ? '<div class="absolute inset-0 bg-black/50 flex items-center justify-center"><i data-lucide="volume-2" class="w-3.5 h-3.5 text-[#35D6FF]"></i></div>' : ''}
                </div>
                <div class="truncate flex-1">
                    <div class="flex items-center space-x-1.5 truncate">
                        <span class="text-xs font-semibold truncate ${isCurrent ? 'text-[#35D6FF]' : 'text-white'}">${this.escapeHtml(track.title)}</span>
                        ${track.vibe_match ? `<span class="text-[8px] font-mono text-[#35D6FF] uppercase px-1 py-0.2 rounded bg-[#35D6FF]/10 border border-[#35D6FF]/20 flex-shrink-0">${track.vibe_match}</span>` : ''}
                    </div>
                    <div class="text-[10px] text-gray-400 truncate">${this.escapeHtml(track.artist)}</div>
                </div>
                <span class="text-[10px] font-mono text-gray-400 flex-shrink-0">${track.formatted_duration || '3:30'}</span>
            `;
            el.onclick = () => {
                this.currentIndex = idx;
                this.playTrack(this.queue[idx], this.queue);
            };
            this.queueListEl.appendChild(el);
        });

        if (window.lucide) lucide.createIcons();
    }

    /* ------- WEB AUDIO API REAL-TIME NEON VISUALIZER ------- */
    ensureAudioContext() {
        if (this.isVisualizerInit) return;
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            this.audioCtx = new AudioCtx();
            this.analyser = this.audioCtx.createAnalyser();
            this.analyser.fftSize = 128;
            this.analyser.smoothingTimeConstant = 0.82;

            this.sourceNode = this.audioCtx.createMediaElementSource(this.audio);
            this.sourceNode.connect(this.analyser);
            this.analyser.connect(this.audioCtx.destination);
            this.isVisualizerInit = true;
        } catch (err) {
            console.log('[WebAudio Init Note]:', err.message);
        }
    }

    startVisualizer() {
        if (!this.visualizerCanvas || !this.canvasCtx) return;
        if (this.animFrameId) cancelAnimationFrame(this.animFrameId);

        const canvas = this.visualizerCanvas;
        const ctx = this.canvasCtx;
        canvas.width = canvas.offsetWidth || 300;
        canvas.height = canvas.offsetHeight || 100;

        const bufferLength = this.analyser ? this.analyser.frequencyBinCount : 32;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            this.animFrameId = requestAnimationFrame(draw);
            
            if (this.analyser && this.isPlaying) {
                this.analyser.getByteFrequencyData(dataArray);
            } else {
                for (let i = 0; i < bufferLength; i++) {
                    dataArray[i] = Math.max(0, dataArray[i] - 2);
                }
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 1.6;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
                
                const grad = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight);
                grad.addColorStop(0, '#9B5CFF');
                grad.addColorStop(0.5, '#35D6FF');
                grad.addColorStop(1, '#FFFFFF');

                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.roundRect(x, canvas.height - barHeight, barWidth - 2, barHeight, [4, 4, 0, 0]);
                ctx.fill();

                x += barWidth;
            }
        };

        draw();
    }

    updateAmbientGlow(track) {
        const disc = document.getElementById('ambient-backdrop-glow');
        if (!disc) return;
        
        const moodColors = {
            'Malayalam': 'rgba(53, 214, 255, 0.25)',
            'Tamil': 'rgba(255, 53, 122, 0.25)',
            'Hindi': 'rgba(245, 158, 11, 0.25)',
            'English': 'rgba(155, 92, 255, 0.25)',
            'Midnight Drive': 'rgba(99, 102, 241, 0.25)',
            'Aurora': 'rgba(16, 185, 129, 0.25)'
        };

        const bg = moodColors[track.language] || moodColors[track.mood] || 'rgba(155, 92, 255, 0.25)';
        disc.style.background = bg;
    }

    /* ------- INITIAL QUEUE LOADER (PERSISTENCE-AWARE) ------- */
    async loadInitialQueue() {
        // Step 1: Check if user already had an active track loaded or playing in localStorage
        const savedTrackRaw = localStorage.getItem('romusic_current_track');
        if (savedTrackRaw) {
            try {
                const savedTrack = JSON.parse(savedTrackRaw);
                if (savedTrack && (savedTrack.title || savedTrack.id)) {
                    this.currentTrack = savedTrack;
                    this.updateMetadataUI(savedTrack);

                    const savedQueue = localStorage.getItem('romusic_queue');
                    if (savedQueue) {
                        try { this.queue = JSON.parse(savedQueue); } catch (e) {}
                    }
                    const savedIndex = localStorage.getItem('romusic_current_index');
                    if (savedIndex !== null) {
                        this.currentIndex = parseInt(savedIndex) || 0;
                    }
                    this.renderQueue();
                    // PRESERVE CURRENT SONG! DO NOT OVERWRITE WITH MALARE!
                    return;
                }
            } catch (e) {
                console.warn('[RoMusic Track Restore Error]:', e);
            }
        }

        // Step 2: Only if no track was ever loaded, load initial catalogue
        try {
            const resp = await fetch('/api/songs');
            const songs = await resp.json();
            if (Array.isArray(songs) && songs.length > 0) {
                this.queue = songs;
                this.currentIndex = 0;
                this.currentTrack = songs[0];
                this.updateMetadataUI(songs[0]);
                this.renderQueue();
            }
        } catch (err) {
            console.warn('[Queue Load Error]:', err);
        }
    }

    /* ------- UTILITY HELPERS ------- */
    formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    showToast(msg) {
        if (window.showToast) {
            window.showToast(msg);
        } else {
            console.log('[Toast]:', msg);
        }
    }

    escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// Global player instance
document.addEventListener('DOMContentLoaded', () => {
    window.player = new RoMusicPlayer();
});
