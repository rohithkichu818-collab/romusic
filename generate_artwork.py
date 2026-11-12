import os

def create_svg_cover(filename, title, subtitle, color1, color2, style='geometric'):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if style == 'aurora':
        elements = f'''
        <defs>
            <radialGradient id="aurora" cx="50%" cy="30%" r="70%">
                <stop offset="0%" stop-color="{color1}" stop-opacity="0.9"/>
                <stop offset="50%" stop-color="{color2}" stop-opacity="0.6"/>
                <stop offset="100%" stop-color="#090B16" stop-opacity="1"/>
            </radialGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="30" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <rect width="600" height="600" fill="#090B16"/>
        <circle cx="300" cy="220" r="180" fill="url(#aurora)" filter="url(#glow)"/>
        <path d="M50 450 Q 200 320, 350 420 T 550 380" stroke="{color1}" stroke-width="6" fill="none" opacity="0.8"/>
        <path d="M50 480 Q 220 360, 380 460 T 550 410" stroke="{color2}" stroke-width="4" fill="none" opacity="0.6"/>
        '''
    elif style == 'orbit':
        elements = f'''
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="{color1}" />
                <stop offset="100%" stop-color="{color2}" />
            </linearGradient>
            <filter id="neon" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="15" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <rect width="600" height="600" fill="#090B16"/>
        <!-- Concentric Cyber Rings -->
        <circle cx="300" cy="260" r="160" stroke="url(#grad1)" stroke-width="2" fill="none" opacity="0.4" stroke-dasharray="10 8"/>
        <circle cx="300" cy="260" r="120" stroke="{color1}" stroke-width="3" fill="none" opacity="0.7"/>
        <circle cx="300" cy="260" r="80" stroke="{color2}" stroke-width="4" fill="url(#grad1)" filter="url(#neon)" opacity="0.85"/>
        <circle cx="300" cy="260" r="30" fill="#090B16"/>
        <circle cx="300" cy="260" r="10" fill="{color1}"/>
        '''
    else: # cyber / waveform
        elements = f'''
        <defs>
            <linearGradient id="cyber" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="{color1}" />
                <stop offset="50%" stop-color="{color2}" />
                <stop offset="100%" stop-color="#35D6FF" />
            </linearGradient>
        </defs>
        <rect width="600" height="600" fill="#090B16"/>
        <rect x="60" y="60" width="480" height="480" rx="28" fill="#111426" stroke="rgba(155, 92, 255, 0.25)" stroke-width="2"/>
        <g transform="translate(100, 200)" fill="url(#cyber)" opacity="0.85">
            <rect x="0" y="80" width="16" height="80" rx="8"/>
            <rect x="30" y="40" width="16" height="120" rx="8"/>
            <rect x="60" y="10" width="16" height="150" rx="8"/>
            <rect x="90" y="50" width="16" height="110" rx="8"/>
            <rect x="120" y="0" width="16" height="160" rx="8"/>
            <rect x="150" y="30" width="16" height="130" rx="8"/>
            <rect x="180" y="70" width="16" height="90" rx="8"/>
            <rect x="210" y="10" width="16" height="150" rx="8"/>
            <rect x="240" y="40" width="16" height="120" rx="8"/>
            <rect x="270" y="60" width="16" height="100" rx="8"/>
            <rect x="300" y="20" width="16" height="140" rx="8"/>
            <rect x="330" y="90" width="16" height="70" rx="8"/>
            <rect x="360" y="110" width="16" height="50" rx="8"/>
        </g>
        '''

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
        {elements}
        <!-- Glass Badge overlay -->
        <rect x="50" y="470" width="500" height="85" rx="18" fill="rgba(17, 20, 38, 0.75)" stroke="rgba(255, 255, 255, 0.12)" stroke-width="1.5"/>
        <text x="80" y="512" font-family="'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="24" font-weight="800" fill="#FFFFFF" letter-spacing="0.5">{title}</text>
        <text x="80" y="538" font-family="'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="14" font-weight="600" fill="{color2}" letter-spacing="2" text-transform="uppercase">{subtitle}</text>
        <circle cx="510" cy="512" r="18" fill="{color1}" opacity="0.9"/>
        <polygon points="506,504 518,512 506,520" fill="#090B16"/>
    </svg>'''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Generated {filename}")

if __name__ == '__main__':
    covers = [
        ('cover_premam.svg', 'MALARE', 'Vijay Yesudas • Rajesh Murugesan', '#9B5CFF', '#35D6FF', 'aurora'),
        ('cover_aavesham.svg', 'JAADA', 'Sushin Shyam • Aavesham Club', '#FF357A', '#35D6FF', 'orbit'),
        ('cover_manjummel.svg', 'KUTHANTHRAM', 'Sushin Shyam • Vedan', '#35D6FF', '#9B5CFF', 'cyber'),
        ('cover_leo.svg', 'BADASS', 'Anirudh Ravichander • LEO', '#FF4444', '#9B5CFF', 'orbit'),
        ('cover_jailer.svg', 'HUKUM', 'Anirudh • Tiger Ka Hukum', '#FFB800', '#FF357A', 'cyber'),
        ('cover_animal.svg', 'ARJAN VAILLY', 'Bhupinder Babbal • ANIMAL', '#FF2A55', '#9B5CFF', 'orbit'),
        ('cover_kesariya.svg', 'KESARIYA', 'Arijit Singh • Pritam', '#FFAE35', '#B57EDC', 'aurora'),
        ('cover_blinding.svg', 'BLINDING LIGHTS', 'The Weeknd • After Hours', '#FF0055', '#35D6FF', 'cyber'),
        ('cover_interstellar.svg', 'INTERSTELLAR', 'Hans Zimmer • Aurora Mix', '#35D6FF', '#B57EDC', 'aurora'),
        ('cover_midnight.svg', 'MIDNIGHT DRIVE', 'ROMUSIC Curated • Synthwave', '#9B5CFF', '#35D6FF', 'orbit'),
        ('cover_default.svg', 'ROMUSIC', 'Next-Gen Sound Architecture', '#9B5CFF', '#35D6FF', 'aurora')
    ]
    covers_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'covers')
    for fname, title, sub, c1, c2, sty in covers:
        create_svg_cover(os.path.join(covers_dir, fname), title, sub, c1, c2, sty)

