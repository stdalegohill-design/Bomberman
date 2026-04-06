"""
Sistema de gestión de audio centralizado.

Este módulo implementa AudioManager, un gestor único que controla toda
la reproducción de música y efectos de sonido del juego. Utiliza pygame.mixer
con un sistema de caché que precarga todos los SFX al inicio para eliminar
lag durante la reproducción en tiempo real.

Arquitectura:
    - Patrón Singleton: Una sola instancia creada en Game
    - Precarga de efectos: Todos los SFX en memoria al iniciar
    - Fade in/out: Transiciones suaves entre pistas musicales
    - Volúmenes independientes: Master, music y sfx por separado

Clases Exportadas:
    - AudioManager: Gestor centralizado de audio

Uso Típico:
    from audio import AudioManager
    
    audio = AudioManager()
    audio.play_music('level_1', fade_ms=1000)
    audio.play_sfx('bomb_explode')

Notas:
    El mixer se inicializa con 44100 Hz, 16-bit signed, stereo, buffer 512.
    Si pygame.mixer falla al inicializar, el AudioManager entra en modo
    silencioso (_ready=False) sin crashear el juego.
"""

import pygame
import os
from settings import AudioConfig, SOUNDS_DIR, MUSIC_DIR, MUSIC_TRACKS, SOUND_EFFECTS


class AudioManager:
    """
    Gestor centralizado de música y efectos de sonido.
    
    Esta clase maneja toda la reproducción de audio del juego usando
    pygame.mixer. Implementa un sistema de caché para SFX que elimina
    lag, y controles independientes para música y efectos.
    
    Se crea UNA sola vez en la clase Game y se pasa como referencia
    a todos los estados y nivel que necesiten reproducir audio.
    
    Attributes:
        music_enabled (bool): Si la música está activada.
        sfx_enabled (bool): Si los efectos están activados.
        master_volume (float): Volumen maestro (0.0-1.0).
        music_volume (float): Volumen de música (0.0-1.0).
        sfx_volume (float): Volumen de efectos (0.0-1.0).
    
    Notas:
        Los atributos protegidos (_ready, _sfx_cache, _current_music)
        son para gestión interna del mixer y no requieren acceso público.
    """

    def __init__(self):
        """
        Inicializa el sistema de audio y precarga efectos de sonido.
        
        Intenta inicializar pygame.mixer. Si falla (sin hardware de audio),
        entra en modo silencioso sin crashear. Precarga todos los SFX
        definidos en settings.SOUND_EFFECTS para evitar lag posterior.
        """
        self._ready = False
        self._sfx_cache = {}           # {nombre: pygame.mixer.Sound}
        self._current_music = None     # nombre de la pista actual

        # Volúmenes configurables en tiempo real
        self.master_volume = AudioConfig.MASTER_VOLUME
        self.music_volume  = AudioConfig.MUSIC_VOLUME
        self.sfx_volume    = AudioConfig.SFX_VOLUME

        self.music_enabled = AudioConfig.MUSIC_ENABLED
        self.sfx_enabled   = AudioConfig.SFX_ENABLED

        self._init_mixer()

    # =========================================================================
    # INICIALIZACIÓN
    # =========================================================================

    def _init_mixer(self):
        """
        Inicializa pygame.mixer con configuración óptima.
        
        Falla silenciosamente si no hay hardware de audio disponible,
        permitiendo que el juego continúe sin sonido.
        
        Raises:
            No lanza excepciones. Captura todos los errores internamente.
        """
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
        """
        Precarga todos los efectos de sonido al inicio.
        
        Itera sobre SOUND_EFFECTS en settings.py y carga cada uno
        en _sfx_cache. Esto elimina lag al reproducir por primera vez.
        """
        for name, filename in SOUND_EFFECTS.items():
            self._load_sfx(name, filename)

    def _load_sfx(self, name: str, filename: str):
        """
        Carga un efecto de sonido individual en el caché.
        
        Args:
            name: Identificador del efecto (ej: 'bomb_place').
            filename: Nombre del archivo en SOUNDS_DIR.
        
        Notas:
            Falla silenciosamente si el archivo no existe, imprimiendo
            advertencia en consola para debugging.
        """
        if not self._ready:
            return
        path = os.path.join(SOUNDS_DIR, filename)
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.sfx_volume * self.master_volume)
            self._sfx_cache[name] = sound
        except Exception as e:
            print(f"SFX '{name}' ({filename}): {e}")

    # =========================================================================
    # MÚSICA
    # =========================================================================

    def play_music(self, track_name: str, loops: int = -1, fade_ms: int = 500):
        """
        Reproduce una pista de música con loop.
        
        Args:
            track_name: Clave en MUSIC_TRACKS (ej: 'menu', 'level_1').
            loops: Repeticiones (-1 = infinito, 0 = una vez).
            fade_ms: Milisegundos de fade-in al iniciar.
        
        Notas:
            Si la pista ya está sonando, no hace nada para evitar
            restart innecesario. Verifica que music_enabled esté activo.
        """
        if not self._ready or not self.music_enabled:
            return

        # Evitar restart si ya está sonando
        if track_name == self._current_music:
            return

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

    def stop_music(self, fade_ms: int = 500):
        """
        Detiene la música con fade-out opcional.
        
        Args:
            fade_ms: Milisegundos de fade-out. 0 para stop inmediato.
        """
        if not self._ready:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self._current_music = None

    def pause_music(self):
        """Pausa la música actual. Reanudar con resume_music()."""
        if self._ready:
            pygame.mixer.music.pause()

    def resume_music(self):
        """Reanuda la música pausada."""
        if self._ready:
            pygame.mixer.music.unpause()

    def is_music_playing(self) -> bool:
        """
        Verifica si hay música reproduciéndose.
        
        Returns:
            True si el mixer está activo y reproduciendo música.
        """
        return self._ready and pygame.mixer.music.get_busy()

    # =========================================================================
    # EFECTOS DE SONIDO
    # =========================================================================

    def play_sfx(self, name: str):
        """
        Reproduce un efecto de sonido.
        
        Busca el efecto en el caché. Si no existe, intenta cargarlo
        dinámicamente. Si sfx_enabled es False, no hace nada.
        
        Args:
            name: Identificador del efecto (ej: 'bomb_place').
        
        Notas:
            Los efectos se pueden reproducir múltiples veces simultáneamente.
            Cada reproducción es independiente (no se cancelan entre sí).
        """
        if not self._ready or not self.sfx_enabled:
            return

        sound = self._sfx_cache.get(name)
        if sound:
            sound.play()
        else:
            # Carga dinámica si no estaba en caché (fallback)
            filename = SOUND_EFFECTS.get(name)
            if filename:
                self._load_sfx(name, filename)
                if name in self._sfx_cache:
                    self._sfx_cache[name].play()

    def stop_sfx(self, name: str):
        """
        Detiene un efecto de sonido específico.
        
        Args:
            name: Identificador del efecto a detener.
        """
        if not self._ready:
            return
        sound = self._sfx_cache.get(name)
        if sound:
            sound.stop()

    def stop_all_sfx(self):
        """Detiene todos los efectos de sonido activos."""
        if self._ready:
            pygame.mixer.stop()

    # =========================================================================
    # CONTROL DE VOLUMEN
    # =========================================================================

    def set_master_volume(self, volume: float):
        """
        Cambia el volumen maestro global.
        
        Actualiza inmediatamente la música y todos los SFX en caché.
        
        Args:
            volume: Volumen entre 0.0 (silencio) y 1.0 (máximo).
        """
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_volumes()

    def set_music_volume(self, volume: float):
        """
        Cambia el volumen de la música.
        
        Args:
            volume: Volumen entre 0.0 y 1.0.
        """
        self.music_volume = max(0.0, min(1.0, volume))
        if self._ready:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)

    def set_sfx_volume(self, volume: float):
        """
        Cambia el volumen de los efectos de sonido.
        
        Actualiza todos los SFX en caché inmediatamente.
        
        Args:
            volume: Volumen entre 0.0 y 1.0.
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sfx_cache.values():
            sound.set_volume(self.sfx_volume * self.master_volume)

    def _apply_volumes(self):
        """
        Recalcula y aplica todos los volúmenes.
        
        Usado internamente cuando se cambia master_volume para
        propagar el cambio a música y todos los efectos.
        """
        if not self._ready:
            return
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
        for sound in self._sfx_cache.values():
            sound.set_volume(self.sfx_volume * self.master_volume)

    def toggle_music(self) -> bool:
        """
        Activa/desactiva la música.
        
        Returns:
            Nuevo estado de music_enabled.
        """
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.pause_music()
        else:
            self.resume_music()
        return self.music_enabled

    def toggle_sfx(self) -> bool:
        """
        Activa/desactiva los efectos de sonido.
        
        Returns:
            Nuevo estado de sfx_enabled.
        """
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def cleanup(self):
        """
        Limpia recursos de audio antes de cerrar el juego.
        
        Detiene música y efectos sin fade, y vacía el caché.
        Llamado automáticamente por Game._cleanup().
        """
        if self._ready:
            self.stop_music(fade_ms=0)
            self.stop_all_sfx()
            self._sfx_cache.clear()

    @property
    def status(self) -> dict:
        """
        Retorna estado actual del sistema de audio.
        
        Útil para debug y para mostrar en menú de opciones.
        
        Returns:
            Diccionario con todos los parámetros de estado.
        """
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