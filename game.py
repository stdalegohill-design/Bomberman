"""
Game Manager principal del proyecto.

Este módulo implementa la clase Game, que actúa como el controlador
central de la aplicación. Gestiona la inicialización de Pygame, el
State Manager para flujo de estados, y el game loop principal con
control de FPS y delta time.

La arquitectura sigue el patrón State donde cada pantalla (menú, juego,
pausa, game over) es un estado independiente. Game orquesta las transiciones
y proporciona recursos compartidos como fuentes, pantalla y audio.

Clases Exportadas:
    - Game: Controlador principal de la aplicación

Funciones Exportadas:
    - main(): Punto de entrada que crea y ejecuta Game

Uso Típico:
    from game import main
    
    if __name__ == "__main__":
        main()

Notas:
    El game loop usa delta time con límite de 50ms por frame para
    prevenir atravesar muros tras lag spikes o garbage collection.
    La validación de settings se ejecuta antes de inicializar Pygame.
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
    """
    Controlador principal de la aplicación Bomberman.
    
    Esta clase centraliza la inicialización de Pygame, gestión de estados,
    y el game loop principal. Proporciona recursos compartidos (pantalla,
    fuentes, audio) a todos los estados del juego.
    
    El loop principal delega toda la lógica a estados específicos usando
    el patrón State, manteniendo Game simple y enfocado en orquestación.
    
    Attributes:
        screen (pygame.Surface): Ventana principal del juego.
        clock (pygame.time.Clock): Reloj para control de FPS.
        running (bool): Flag de ejecución del game loop.
        num_players (int): Cantidad de jugadores (1-4).
        difficulty (str): Dificultad actual ('easy', 'normal', 'hard').
        font_large (pygame.font.Font): Fuente grande para títulos.
        font (pygame.font.Font): Fuente mediana para opciones.
        font_small (pygame.font.Font): Fuente pequeña para hints.
        state_manager (StateManager): Gestor de transiciones de estado.
        states (dict): Mapa de nombres a instancias de estados.
        audio (AudioManager): Gestor centralizado de audio.
    
    Notas:
        Se crea UNA sola instancia de Game por ejecución.
        Los atributos de estado (num_players, difficulty) se actualizan
        desde los menús de selección antes de iniciar el gameplay.
    """
    
    def __init__(self):
        """
        Inicializa Pygame, recursos compartidos y State Manager.
        
        Orden de inicialización:
        1. Validación de configuración (settings.py)
        2. Pygame.init() y pygame.mixer.init()
        3. Ventana y reloj
        4. Fuentes pixel-art
        5. AudioManager
        6. State Manager y todos los estados
        7. Transición a estado MENU
        
        Raises:
            pygame.error: Si Pygame no puede inicializarse.
            FileNotFoundError: Si faltan archivos críticos de assets.
        """
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
        Carga fuentes pixel-art con fallback a fuentes del sistema.
        
        Intenta cargar 'Press Start 2P' desde assets/fonts/. Si no existe,
        usa Courier New (o Courier o monospace según disponibilidad).
        Como último recurso usa pygame.font.Font(None) con ajuste de tamaño.
        
        Crea tres tamaños:
        - font_large (22pt): Títulos como "BOMBER/MAN"
        - font (16pt): Opciones de menú
        - font_small (10pt): Hints y estadísticas
        
        Notas:
            El fallback garantiza que el juego funcione sin assets,
            útil para testing y distribución mínima.
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
        """
        Crea State Manager y todas las instancias de estados.
        
        Orden crítico:
        1. Crear StateManager
        2. Instanciar todos los estados (reciben self como game)
        3. Registrar estados en el manager
        4. Crear AudioManager (los estados lo usan en enter())
        5. Cambiar a estado MENU inicial
        
        Notas:
            AudioManager debe crearse ANTES de change_state(MENU)
            porque MenuState.enter() reproduce música inmediatamente.
        """
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
        Ejecuta el game loop principal con control de FPS.
        
        El loop delega toda la lógica de gameplay a estados específicos
        usando el patrón State. Game solo se encarga de:
        - Calcular delta time con protección anti-lag
        - Recopilar eventos de pygame
        - Delegar handle_events/update/draw al estado actual
        - Actualizar la pantalla
        
        Delta time está limitado a 50ms para prevenir que entidades
        atraviesen muros tras lag spikes o garbage collection de Python.
        
        Notas:
            El loop termina cuando self.running = False (llamado por quit()).
            Ejecuta _cleanup() automáticamente al salir.
        """
        print("\nINICIANDO GAME LOOP")
        print("="*60)
        
        while self.running:
            # Calcular delta time en segundos
            dt = self.clock.tick(FPS) / 1000.0
            
            # Limitar a 50ms para prevenir atravesar muros tras lag spikes
            # o pausas por garbage collection. Sin esto, un frame de 200ms
            # podría mover al jugador 6+ celdas en un solo update.
            dt = min(dt, 0.05)
            
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
    Punto de entrada principal de la aplicación.
    
    Crea una instancia de Game y ejecuta su game loop.
    Captura excepciones para cleanup ordenado y mensajes de error claros.
    
    Excepciones manejadas:
    - KeyboardInterrupt: Ctrl+C del usuario
    - Exception: Cualquier error fatal con traceback
    
    Cleanup garantizado:
    - pygame.quit() en bloque finally
    - sys.exit() para terminar proceso
    
    Notas:
        Esta función es llamada desde main.py, que es el entry point
        del ejecutable. La separación permite testing más fácil.
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