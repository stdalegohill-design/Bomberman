"""
AUDIO.PY - Sistema de Música y Efectos de Sonido
=================================================

Maneja todo el audio del juego desde un único lugar:
- Música de fondo por estado (menú, juego, game over...)
- Efectos de sonido con volumen independiente
- Activar/desactivar música y SFX por separado
- Fade in/out de música

Uso:
    from audio import AudioManager
    audio = AudioManager()          # Inicializar una sola vez en Game
    audio.play_music('menu')        # Reproducir pista
    audio.play_sfx('bomb_place')    # Reproducir efecto
"""

import pygame
import os
from settings import AudioConfig, SOUNDS_DIR, MUSIC_DIR, MUSIC_TRACKS, SOUND_EFFECTS


class AudioManager:
    """
    Gestor centralizado de audio.
    Se crea UNA sola vez en Game y se pasa a los estados/nivel.
    """

    def __init__(self):
        self._ready = False
        self._sfx_cache = {}           # {nombre: pygame.mixer.Sound}
        self._current_music = None     # nombre de la pista actual

        # Volúmenes actuales (se pueden cambiar en tiempo real)
        self.master_volume = AudioConfig.MASTER_VOLUME
        self.music_volume  = AudioConfig.MUSIC_VOLUME
        self.sfx_volume    = AudioConfig.SFX_VOLUME

        self.music_enabled = AudioConfig.MUSIC_ENABLED
        self.sfx_enabled   = AudioConfig.SFX_ENABLED

        self._init_mixer()

    # INICIALIZACIÓN

    def _init_mixer(self):
        """Inicializa pygame.mixer. Falla silenciosamente si no hay audio."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._ready = True
            print("AudioManager inicializado")
            self._preload_sfx()
        except Exception as e:
            print(f"AudioManager: no se pudo inicializar el mixer: {e}")
            self._ready = False

    def _preload_sfx(self):
        """Carga todos los SFX al inicio para evitar lag al reproducirlos."""
        for name, filename in SOUND_EFFECTS.items():
            self._load_sfx(name, filename)

    def _load_sfx(self, name, filename):
        """Carga un SFX en cache. Falla silenciosamente si el archivo no existe."""
        if not self._ready:
            return
        path = os.path.join(SOUNDS_DIR, filename)
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.sfx_volume * self.master_volume)
            self._sfx_cache[name] = sound
        except Exception as e:
            print(f"SFX '{name}' ({filename}): {e}")

    # MÚSICA

    def play_music(self, track_name, loops=-1, fade_ms=500):
        """
        Reproduce una pista de música en loop.

        Args:
            track_name: Clave de MUSIC_TRACKS (ej: 'menu', 'level_1')
            loops: -1 = loop infinito, 0 = una vez
            fade_ms: Milisegundos de fade-in
        """
        if not self._ready or not self.music_enabled:
            return

        if track_name == self._current_music:
            return  # Ya está sonando esta pista

        filename = MUSIC_TRACKS.get(track_name)
        if not filename:
            print(f"Pista '{track_name}' no definida en MUSIC_TRACKS")
            return

        path = os.path.join(MUSIC_DIR, filename)
        if not os.path.exists(path):
            print(f"Música '{track_name}' no encontrada: {path}")
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self._current_music = track_name
            print(f"Música: '{track_name}'")
        except Exception as e:
            print(f"Error reproduciendo música '{track_name}': {e}")

    def stop_music(self, fade_ms=500):
        """Detiene la música con fade-out opcional."""
        if not self._ready:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self._current_music = None

    def pause_music(self):
        """Pausa la música (se reanuda con resume_music)."""
        if self._ready:
            pygame.mixer.music.pause()

    def resume_music(self):
        """Reanuda la música pausada."""
        if self._ready:
            pygame.mixer.music.unpause()

    def is_music_playing(self):
        """Retorna True si hay música reproduciéndose."""
        return self._ready and pygame.mixer.music.get_busy()

    # EFECTOS DE SONIDO

    def play_sfx(self, name):
        """
        Reproduce un efecto de sonido.

        Args:
            name: Clave de SOUND_EFFECTS (ej: 'bomb_place', 'explosion')
        """
        if not self._ready or not self.sfx_enabled:
            return

        sound = self._sfx_cache.get(name)
        if sound:
            sound.play()
        else:
            # Intentar cargar si no estaba en cache
            filename = SOUND_EFFECTS.get(name)
            if filename:
                self._load_sfx(name, filename)
                if name in self._sfx_cache:
                    self._sfx_cache[name].play()

    def stop_sfx(self, name):
        """Detiene un SFX específico."""
        if not self._ready:
            return
        sound = self._sfx_cache.get(name)
        if sound:
            sound.stop()

    def stop_all_sfx(self):
        """Detiene todos los efectos activos."""
        if self._ready:
            pygame.mixer.stop()

    # CONTROL DE VOLUMEN

    def set_master_volume(self, volume):
        """
        Cambia el volumen maestro (0.0 a 1.0).
        Actualiza música y todos los SFX en cache.
        """
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_volumes()

    def set_music_volume(self, volume):
        """Cambia el volumen de la música (0.0 a 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if self._ready:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)

    def set_sfx_volume(self, volume):
        """Cambia el volumen de los SFX (0.0 a 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sfx_cache.values():
            sound.set_volume(self.sfx_volume * self.master_volume)

    def _apply_volumes(self):
        """Recalcula y aplica todos los volúmenes."""
        if not self._ready:
            return
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
        for sound in self._sfx_cache.values():
            sound.set_volume(self.sfx_volume * self.master_volume)

    def toggle_music(self):
        """Activa/desactiva la música."""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.pause_music()
        else:
            self.resume_music()
        return self.music_enabled

    def toggle_sfx(self):
        """Activa/desactiva los efectos de sonido."""
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled

    # UTILIDADES

    def cleanup(self):
        """Limpia recursos de audio."""
        if self._ready:
            self.stop_music(fade_ms=0)
            self.stop_all_sfx()
            self._sfx_cache.clear()

    @property
    def status(self):
        """Retorna un dict con el estado actual del audio (para debug/UI)."""
        return {
            'ready':         self._ready,
            'music_enabled': self.music_enabled,
            'sfx_enabled':   self.sfx_enabled,
            'current_music': self._current_music,
            'master_volume': self.master_volume,
            'music_volume':  self.music_volume,
            'sfx_volume':    self.sfx_volume,
            'sfx_loaded':    list(self._sfx_cache.keys()),
        }