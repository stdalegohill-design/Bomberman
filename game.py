"""
GAME.PY - Game Manager Principal
=================================

Clase principal que gestiona:
- Inicialización de Pygame
- State Manager
- Game Loop principal
- Recursos compartidos (fuentes, pantalla)
"""

import pygame
import sys
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    GameStates, Colors, validate_settings, get_config_summary
)
from audio import AudioManager
from states import (
    PlayerSelectState, DifficultySelectState,
    MenuState, PlayingState, PausedState,
    GameOverState, VictoryState, StateManager
)


class Game:
    """Clase principal del juego."""
    
    def __init__(self):
        """Inicializa el juego."""
        print("\n" + "="*60)
        print("INICIALIZANDO BOMBERMAN")
        print("="*60)
        
        # Validar configuración
        validate_settings()
        
        # Inicializar Pygame
        pygame.init()
        pygame.mixer.init()  # Para audio futuro
        
        # Crear ventana
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Clock para FPS
        self.clock = pygame.time.Clock()
        self.running = True
        self.num_players = 1   # Se actualiza desde el menú
        self.difficulty = 'NORMAL'  # Sistema de dificultad
        
        # Fuentes
        self._init_fonts()
        
        # State Manager
        self._init_states()
        
        print("="*60)
        print("Inicialización completa")
        print(get_config_summary())
        print("="*60 + "\n")
    
    def _init_fonts(self):
        """
        Fuentes pixel-art estilo Bomberman retro.
        Usa 'Press Start 2P' si existe en assets/fonts/PressStart2P.ttf,
        si no cae a Courier New (monoespaciado).
        """
        import os
        pixel_font_path = os.path.join('assets', 'fonts', 'PressStart2P.ttf')

        def make_font(size):
            if os.path.isfile(pixel_font_path):
                return pygame.font.Font(pixel_font_path, size)
            for name in ['Courier New', 'Courier', 'monospace']:
                try:
                    f = pygame.font.SysFont(name, size)
                    if f: return f
                except: pass
            return pygame.font.Font(None, size + 6)

        self.font_large = make_font(22)   # Titulos (BOMBER/MAN, DIFICULTAD...)
        self.font       = make_font(16)   # Opciones de menu (JUGAR, SALIR...)
        self.font_small = make_font(10)   # Hints / controles / stats

        print(f"Fuentes pixel (PressStart2P: {os.path.isfile(pixel_font_path)})")
    
    def _init_states(self):
        """Inicializa el State Manager y todos los estados."""
        self.state_manager = StateManager(self)
        
        # Crear todos los estados
        self.states = {
            GameStates.MENU:               MenuState(self),
            GameStates.DIFFICULTY_SELECT:  DifficultySelectState(self),
            GameStates.PLAYER_SELECT:      PlayerSelectState(self),
            GameStates.PLAYING:            PlayingState(self),
            GameStates.PAUSED:             PausedState(self),
            GameStates.GAMEOVER:           GameOverState(self),
            GameStates.VICTORY:            VictoryState(self),
        }
        
        # Registrar estados en el manager
        for name, state in self.states.items():
            self.state_manager.add_state(name, state)
        
        # Audio PRIMERO: los estados lo usan en enter()
        self.audio = AudioManager()

        # Comenzar en el menú (llama a MenuState.enter → usa self.audio)
        self.state_manager.change_state(GameStates.MENU)
        
        print("State Manager inicializado")
        print(f"   Estados disponibles: {list(self.states.keys())}")
    
    # CONTROL DE ESTADOS
    
    def change_state(self, new_state):
        """
        Cambia el estado del juego.
        
        Args:
            new_state: Nombre del nuevo estado (de GameStates)
        """
        self.state_manager.change_state(new_state)
    
    def get_current_state_name(self):
        """
        Obtiene el nombre del estado actual.
        
        Returns:
            str: Nombre del estado actual
        """
        for name, state in self.states.items():
            if state == self.state_manager.current_state:
                return name
        return None
    
    # GAME LOOP
    
    def run(self):
        """
        Loop principal del juego.
        
        Este loop es MUCHO más simple que el anterior gracias
        al State Pattern. Toda la lógica está delegada a los estados.
        """
        print("\nINICIANDO GAME LOOP")
        print("="*60)
        
        while self.running:
            # Delta time con protección contra lag spikes
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Máximo 50ms por frame (previene saltos de física)
            
            # Eventos
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()
            
            # Delegar al estado actual
            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            self.state_manager.draw()
            
            # Actualizar pantalla
            pygame.display.flip()
        
        # Cleanup
        self._cleanup()
    
    def quit(self):
        """Cierra el juego de manera ordenada."""
        print("\n" + "="*60)
        print("Cerrando Bomberman")
        print("="*60)
        self.running = False
    
    def _cleanup(self):
        """Limpia recursos antes de cerrar."""
        # Limpiar estado actual
        if self.state_manager.current_state:
            self.state_manager.current_state.exit()
        
        # Limpiar audio
        self.audio.cleanup()

        # Cerrar Pygame
        pygame.mixer.quit()
        pygame.quit()
        sys.exit()
    
    # UTILIDADES
    
    def get_fps(self):
        """
        Obtiene los FPS actuales.
        
        Returns:
            int: FPS
        """
        return int(self.clock.get_fps())
    
    def reset_game(self):
        """Reinicia el juego completo."""
        print("\nREINICIANDO JUEGO")
        
        # Salir del estado actual
        if self.state_manager.current_state:
            self.state_manager.current_state.exit()
        
        # Re-inicializar estado de juego
        self.states[GameStates.PLAYING] = PlayingState(self)
        self.state_manager.add_state(GameStates.PLAYING, self.states[GameStates.PLAYING])
        
        # Volver al menú
        self.change_state(GameStates.MENU)
        
        print("Juego reiniciado")


# FUNCIONES AUXILIARES

def main():
    """
    Función principal de entrada.
    Crea y ejecuta el juego.
    """
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n\nJuego interrumpido por el usuario")
    except Exception as e:
        print(f"\n\nERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()