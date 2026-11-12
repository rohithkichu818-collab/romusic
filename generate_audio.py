import os
import math
import wave
import struct

def generate_track(filename, duration=15, track_type='synthwave'):
    """
    Generate pleasant multi-tone musical WAV files using Python's standard library.
    duration: duration in seconds
    track_type: 'synthwave', 'aurora', 'chillbeat', 'lofi'
    """
    sample_rate = 44100
    total_samples = int(sample_rate * duration)
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Musical chord progressions (frequencies in Hz)
    progressions = {
        'synthwave': [
            (220.00, 261.63, 329.63, 110.00), # Am (A3, C4, E4, A2)
            (174.61, 220.00, 261.63, 87.31),  # F  (F3, A3, C4, F2)
            (261.63, 329.63, 392.00, 130.81), # C  (C4, E4, G4, C3)
            (196.00, 246.94, 293.66, 98.00),  # G  (G3, B3, D4, G2)
        ],
        'aurora': [
            (293.66, 369.99, 440.00, 146.83), # Dm (D4, F#4, A4, D3)
            (246.94, 311.13, 369.99, 123.47), # Bm
            (196.00, 246.94, 293.66, 98.00),  # G
            (220.00, 277.18, 329.63, 110.00)  # A
        ],
        'chillbeat': [
            (261.63, 329.63, 392.00, 65.41),  # Cmaj7
            (220.00, 261.63, 329.63, 55.00),  # Am7
            (174.61, 220.00, 261.63, 43.65),  # Fmaj7
            (196.00, 246.94, 293.66, 49.00)   # G7
        ],
        'lofi': [
            (329.63, 392.00, 493.88, 82.41),  # Em
            (261.63, 329.63, 392.00, 65.41),  # C
            (220.00, 261.63, 329.63, 55.00),  # Am
            (246.94, 293.66, 369.99, 61.74)   # Bm
        ]
    }
    
    chords = progressions.get(track_type, progressions['synthwave'])
    chord_len = duration / len(chords)
    
    with wave.open(filename, 'w') as wav_file:
        nchannels = 2  # Stereo
        sampwidth = 2  # 16-bit
        wav_file.setparams((nchannels, sampwidth, sample_rate, total_samples, 'NONE', 'not compressed'))
        
        frames = bytearray()
        
        for i in range(total_samples):
            t = i / sample_rate
            chord_idx = int((t / chord_len) % len(chords))
            f1, f2, f3, bass_f = chords[chord_idx]
            
            # Envelope within each chord measure
            chord_t = t % chord_len
            env = math.sin(math.pi * (chord_t / chord_len)) ** 0.5
            
            # Arpeggiator note
            arp_speed = 4.0 # 4 notes per second
            arp_notes = [f1, f2, f3, f2 * 1.5]
            curr_arp = arp_notes[int(t * arp_speed) % 4]
            
            # Left & Right audio synthesis
            # Pad / Chords
            lead = 0.25 * math.sin(2 * math.pi * curr_arp * t)
            pad1 = 0.18 * math.sin(2 * math.pi * f1 * t + 0.1 * math.sin(2 * math.pi * 1.5 * t))
            pad2 = 0.15 * math.sin(2 * math.pi * f2 * t)
            pad3 = 0.12 * math.sin(2 * math.pi * f3 * t)
            
            # Warm rich Bass
            bass = 0.35 * (math.sin(2 * math.pi * bass_f * t) + 0.3 * math.sin(2 * math.pi * bass_f * 2 * t))
            
            # Subtle rhythmic click / beat
            beat_env = max(0, 1.0 - (t % 0.5) * 8.0)
            beat = 0.20 * (math.sin(2 * math.pi * 55 * t) * beat_env)
            
            # Stereo separation
            left_sample = (lead * 0.8 + pad1 + pad2 * 0.5 + bass + beat) * env
            right_sample = (lead * 0.5 + pad2 * 0.7 + pad3 + bass + beat) * env
            
            # Overall fade in and fade out
            if t < 0.5:
                master_fade = t / 0.5
            elif t > duration - 0.8:
                master_fade = max(0, (duration - t) / 0.8)
            else:
                master_fade = 1.0
                
            left_sample *= master_fade
            right_sample *= master_fade
            
            # Clipping protection
            left_sample = max(-0.95, min(0.95, left_sample))
            right_sample = max(-0.95, min(0.95, right_sample))
            
            # Convert to 16-bit integer
            left_int = int(left_sample * 32767)
            right_int = int(right_sample * 32767)
            
            frames.extend(struct.pack('<hh', left_int, right_int))
            
        wav_file.writeframes(frames)
    print(f"Generated {filename}")

if __name__ == '__main__':
    music_dir = os.path.join(os.path.dirname(__file__), 'music')
    tracks = [
        ('malare_aurora.wav', 25, 'aurora'),
        ('jaada_neon.wav', 20, 'synthwave'),
        ('kuthanthram_vibe.wav', 22, 'chillbeat'),
        ('badass_bass.wav', 24, 'synthwave'),
        ('hukum_groove.wav', 22, 'lofi'),
        ('arjan_pulse.wav', 20, 'synthwave'),
        ('kesariya_luxe.wav', 25, 'aurora'),
        ('blinding_neon.wav', 22, 'synthwave'),
        ('interstellar_dream.wav', 28, 'aurora'),
        ('midnight_drive_cyber.wav', 26, 'synthwave')
    ]
    for track_name, dur, style in tracks:
        generate_track(os.path.join(music_dir, track_name), dur, style)

