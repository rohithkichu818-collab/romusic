/* ========================================================
   ROMUSIC — CLIENT APPLICATION & MICRO-INTERACTIONS
   ======================================================== */

// Toast notification helper
window.showToast = function(message, type = 'info') {
    let toast = document.getElementById('romusic-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'romusic-toast';
        toast.className = 'fixed top-6 right-6 z-50 flex items-center space-x-3 px-5 py-3 rounded-2xl glass-panel-elevated shadow-2xl text-sm font-medium border border-[#9B5CFF]/40 text-white';
        document.body.appendChild(toast);
    }
    
    const icon = type === 'success' ? 'check-circle' : 'info';
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 text-[#35D6FF]"></i>
        <span>${message}</span>
    `;
    
    if (window.lucide) lucide.createIcons();
    toast.classList.add('toast-visible');

    setTimeout(() => {
        toast.classList.remove('toast-visible');
    }, 3200);
};

// Create Playlist Modal Controller
window.openCreatePlaylistModal = function() {
    const modal = document.getElementById('create-playlist-modal');
    if (modal) modal.classList.remove('hidden');
};

window.closeCreatePlaylistModal = function() {
    const modal = document.getElementById('create-playlist-modal');
    if (modal) modal.classList.add('hidden');
};

window.submitCreatePlaylist = async function(e) {
    if (e) e.preventDefault();
    const nameInput = document.getElementById('new-playlist-name');
    const descInput = document.getElementById('new-playlist-desc');
    const name = nameInput ? nameInput.value.trim() : '';
    const desc = descInput ? descInput.value.trim() : '';

    if (!name) {
        window.showToast('Please enter a playlist name', 'error');
        return;
    }

    try {
        const res = await fetch('/api/playlists', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, description: desc })
        });
        if (res.ok) {
            window.showToast(`Playlist "${name}" created!`, 'success');
            window.closeCreatePlaylistModal();
            setTimeout(() => window.location.reload(), 600);
        } else if (res.status === 401) {
            window.showToast('Please sign in to create playlists.');
        }
    } catch (err) {
        window.showToast('Failed to create playlist.', 'error');
    }
};

// Add to Playlist modal/action
window.addToPlaylist = async function(playlistId, songId) {
    try {
        const res = await fetch(`/api/playlist/${playlistId}/add/${songId}`, { method: 'POST' });
        if (res.ok) {
            window.showToast('Track added to playlist', 'success');
        } else {
            window.showToast('Could not add track', 'error');
        }
    } catch (e) {
        window.showToast('Network error', 'error');
    }
};

// Instant Live Search Dropdown Handler
window.initLiveSearch = function() {
    const searchInputs = document.querySelectorAll('.romusic-live-search');
    searchInputs.forEach(input => {
        let debounceTimer;
        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const val = e.target.value.trim();
            const resultsDropdown = document.getElementById('search-instant-results');
            if (!resultsDropdown) return;

            if (val.length < 2) {
                resultsDropdown.classList.add('hidden');
                return;
            }

            debounceTimer = setTimeout(async () => {
                try {
                    // Search local catalog first
                    const res = await fetch(`/api/search?q=${encodeURIComponent(val)}`);
                    let tracks = [];
                    if (res.ok) {
                        tracks = await res.json();
                    }

                    // If few local results, supplement with YouTube search
                    if (tracks.length < 4) {
                        try {
                            const ytRes = await fetch(`/api/yt/search?q=${encodeURIComponent(val)}&limit=4`);
                            if (ytRes.ok) {
                                const ytTracks = await ytRes.json();
                                if (Array.isArray(ytTracks)) {
                                    tracks = tracks.concat(ytTracks);
                                }
                            }
                        } catch(e) {}
                    }

                    renderInstantSearchResults(tracks, resultsDropdown);
                } catch (err) {
                    console.error('Search error:', err);
                }
            }, 300);
        });
    });
};

function renderInstantSearchResults(tracks, container) {
    if (!tracks || tracks.length === 0) {
        container.innerHTML = '<div class="p-4 text-xs text-gray-400">Press Enter to explore the global catalog.</div>';
        container.classList.remove('hidden');
        return;
    }

    let html = '<div class="p-2 space-y-1">';
    tracks.slice(0, 7).forEach(track => {
        const isYT = track.source === 'youtube' || Boolean(track.youtube_id);
        const sourceBadge = isYT 
            ? '<span class="text-[9px] font-mono text-[#35D6FF] font-bold ml-1.5 px-1.5 py-0.2 rounded bg-[#35D6FF]/10">Global HQ</span>' 
            : '<span class="text-[9px] font-mono text-[#9B5CFF] font-bold ml-1.5 px-1.5 py-0.2 rounded bg-[#9B5CFF]/10">Vault</span>';

        html += `
            <div class="flex items-center justify-between p-2 rounded-xl hover:bg-[#9B5CFF]/20 transition cursor-pointer" onclick='window.player.playTrack(${JSON.stringify(track).replace(/'/g, "&#39;")})'>
                <div class="flex items-center space-x-3 overflow-hidden">
                    <img src="${track.cover_url || '/static/images/covers/cover_default.svg'}" class="w-10 h-10 rounded-lg object-cover flex-shrink-0" onerror="this.src='/static/images/covers/cover_default.svg'" />
                    <div class="truncate">
                        <div class="text-sm font-semibold text-white truncate flex items-center">${track.title} ${sourceBadge}</div>
                        <div class="text-xs text-gray-400 truncate">${track.artist || ''}</div>
                    </div>
                </div>
                <button class="p-2 text-[#35D6FF] hover:scale-110 transition"><i data-lucide="play" class="w-4 h-4 fill-current"></i></button>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
    container.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

// Sidebar toggle for tablet/desktop
window.toggleSidebar = function() {
    const sidebar = document.getElementById('main-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('-translate-x-full');
    }
};

// ========================================================
// SPA NAVIGATION ROUTER (Zero Audio Interruption Engine)
// Keeps active playback (e.g. Kalyani) alive across all pages!
// ========================================================
window.navigateTo = async function(url, pushState = true) {
    try {
        const res = await fetch(url);
        if (!res.ok) {
            window.location.href = url;
            return;
        }
        const text = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        const newMain = doc.querySelector('main');
        const currentMain = document.querySelector('main');

        if (newMain && currentMain) {
            currentMain.innerHTML = newMain.innerHTML;
            document.title = doc.title;

            if (pushState) {
                history.pushState({ url }, doc.title, url);
            }

            // Update active states on sidebar and mobile bottom nav
            const navLinks = document.querySelectorAll('#main-sidebar a, nav a');
            navLinks.forEach(a => {
                const href = a.getAttribute('href');
                const isMatch = href && (href === url || (url.startsWith(href) && href !== '/'));
                if (a.closest('#main-sidebar')) {
                    if (isMatch) {
                        a.classList.add('bg-gradient-to-r', 'from-[#9B5CFF]/30', 'to-[#35D6FF]/10', 'text-white', 'border-l-4', 'border-[#35D6FF]');
                        a.classList.remove('text-gray-300', 'hover:bg-white/5');
                    } else {
                        a.classList.remove('bg-gradient-to-r', 'from-[#9B5CFF]/30', 'to-[#35D6FF]/10', 'text-white', 'border-l-4', 'border-[#35D6FF]');
                        a.classList.add('text-gray-300');
                    }
                } else if (a.closest('nav')) {
                    a.classList.toggle('text-[#35D6FF]', Boolean(isMatch));
                    a.classList.toggle('text-gray-400', !isMatch);
                }
            });

            // Re-execute scripts inside main
            const scripts = currentMain.querySelectorAll('script');
            scripts.forEach(oldScript => {
                const newScript = document.createElement('script');
                Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });

            if (window.lucide) lucide.createIcons();
            currentMain.scrollTop = 0;
            window.initLiveSearch();
        } else {
            window.location.href = url;
        }
    } catch (err) {
        console.warn('[SPA Navigate fallback]:', err);
        window.location.href = url;
    }
};

window.addEventListener('popstate', () => {
    window.navigateTo(window.location.href, false);
});

document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) lucide.createIcons();
    window.initLiveSearch();

    // Intercept internal page navigation links so audio never stops!
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && !e.defaultPrevented) {
            const href = link.getAttribute('href');
            if (
                href &&
                !href.startsWith('#') &&
                !href.startsWith('javascript:') &&
                !href.startsWith('mailto:') &&
                !href.startsWith('tel:') &&
                !link.hasAttribute('download') &&
                link.target !== '_blank' &&
                link.origin === window.location.origin &&
                !href.startsWith('/logout') &&
                !href.startsWith('/login') &&
                !href.startsWith('/register')
            ) {
                e.preventDefault();
                window.navigateTo(href);
                return;
            }
        }
    });

    // Intercept top search bar form to preserve playback
    const searchForm = document.getElementById('search-bar-container');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = searchForm.querySelector('input[name="q"]');
            const q = input ? input.value.trim() : '';
            if (q) {
                window.navigateTo(`/search?q=${encodeURIComponent(q)}`);
                const dropdown = document.getElementById('search-instant-results');
                if (dropdown) dropdown.classList.add('hidden');
            }
        });
    }

    // Delegated click handler for play-song buttons and cards
    document.addEventListener('click', (e) => {
        const playBtn = e.target.closest('[data-action="play-song"]');
        if (playBtn) {
            e.preventDefault();
            try {
                const rawSong = playBtn.getAttribute('data-song');
                if (rawSong) {
                    const song = JSON.parse(rawSong);
                    if (window.player) {
                        window.player.playTrack(song);
                    }
                }
            } catch (err) {
                console.error('Play track click error:', err);
            }
        }
    });

    // Close search dropdown on click outside
    document.addEventListener('click', (e) => {
        const resultsDropdown = document.getElementById('search-instant-results');
        if (resultsDropdown && !e.target.closest('#search-bar-container')) {
            resultsDropdown.classList.add('hidden');
        }
    });
});

