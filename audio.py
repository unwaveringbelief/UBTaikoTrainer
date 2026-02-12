import pygame
import os
import array
import math
import sys

# --- PYINSTALLER PATH FIX ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AudioManager:
    """
    Manages high-performance audio playback.
    Optimized for low latency in rhythm games using a reduced buffer size (512).
    """
    def __init__(self):
        # Initialize the mixer with a low buffer to minimize input-to-audio lag.
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
        except:
            # Fallback if pre_init is not supported by the system
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            
        self.sounds = {}
        self.volumes = {"don": 0.8, "ka": 0.8, "metro": 0.5}
        
        # Load sounds, prioritizing generated .wav files, then falling back to .ogg
        # We use resource_path() to wrap every file path!
        self.load_sound_flexible("don", [resource_path("assets/don.wav"), resource_path("assets/don.ogg")], 200, 'square')
        self.load_sound_flexible("ka", [resource_path("assets/ka.wav"), resource_path("assets/ka.ogg")], 450, 'square')
        self.load_sound_flexible("metro_tick", [resource_path("assets/metronome.wav"), resource_path("assets/metronome.ogg")], 800, 'sin')

    def load_sound_flexible(self, name, paths, fallback_freq, wave):
        """
        Searches for a sound in a list of paths. 
        If none are found, it automatically generates a synthetic tone.
        """
        sound_loaded = False
        for path in paths:
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    sound_loaded = True
                    break  # Exit on the first successfully loaded file
                except:
                    continue
        
        if not sound_loaded:
            # If no file exists or is readable, use the internal synthesizer
            self.sounds[name] = self.generate_tone(fallback_freq, wave_type=wave)

    def generate_tone(self, freq, duration=0.08, wave_type='sin'):
        """Generates a clean procedural tone as an emergency audio fallback."""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            val = math.sin(2 * math.pi * freq * i / sample_rate)
            if wave_type == 'square': 
                val = 1.0 if val > 0 else -1.0
            
            # Fade-out envelope to prevent audio "clicks" or popping at the end of the sound
            envelope = 1.0 - (i / n_samples) 
            buf[i] = int(32767 * 0.4 * val * envelope)
            
        return pygame.mixer.Sound(buf)

    def play(self, name):
        """Plays a preloaded sound using the current volume setting."""
        if name in self.sounds:
            vol_key = "metro" if "metro" in name else name
            self.sounds[name].set_volume(self.volumes.get(vol_key, 0.5))
            self.sounds[name].play()

    def set_volume(self, key, val):
        """Updates the internal volume mapping for real-time adjustments."""
        self.volumes[key] = val