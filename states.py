"""
Sistema de gestión de estados del juego.

Este módulo implementa el patrón State para manejar las diferentes
pantallas y flujos del juego (menú, selección, gameplay, pausa, etc.).
Cada estado es una clase independiente que maneja su propia lógica de
input, update y renderizado.

Arquitectura:
    StateManager orquesta transiciones entre estados, llamando enter()
    y exit() automáticamente. Los estados reciben una referencia a Game
    para acceder a recursos compartidos (screen, fonts, audio).

Jerarquía de Estados:
    State (Clase Base Abstracta)
        - MenuState: Menú principal con opciones
        - DifficultySelectState: Selección de dificultad
        - PlayerSelectState: Selección de cantidad de jugadores
        - PlayingState: Gameplay activo con GameLevelManager
        - PausedState: Pausa durante gameplay
        - GameOverState: Pantalla de derrota
        - VictoryState: Pantalla de victoria

Clases Exportadas:
    - State: Clase base abstracta
    - StateManager: Gestor de transiciones
    - MenuState: Menú principal
    - DifficultySelectState: Selector de dificultad
    - PlayerSelectState: Selector de jugadores
    - PlayingState: Estado de juego activo
    - PausedState: Pausa
    - GameOverState: Pantalla de derrota
    - VictoryState: Pantalla de victoria

Uso Típico:
    # En Game.__init__
    manager = StateManager(game)
    manager.add_state('MENU', MenuState(game))
    manager.change_state('MENU')
    
    # En game loop
    manager.handle_events(events)
    manager.update(dt)
    manager.draw()

Notas:
    Los estados no deben mantener lógica de juego compleja. PlayingState
    delega todo a GameLevelManager. Los otros estados son principalmente
    UI y navegación.
"""


import pygame
from settings import (
    Colors, GameStates, WINDOW_WIDTH, WINDOW_HEIGHT,
    BombermanConfig, Controls, PlayerConfig,
    DifficultyConfig  # Sistema de dificultad
)
from utils import draw_text, draw_text_multiline

# BASE STATE CLASS

class State:
    """Clase base para todos los estados del juego."""
    
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.font_large = game.font_large
        self.font_small = game.font_small
    
    def handle_events(self, events):
        """
        Maneja eventos de pygame.
        
        Args:
            events: Lista de eventos de pygame
        """
        pass
    
    def update(self, dt):
        """
        Actualiza la lógica del estado.
        
        Args:
            dt: Delta time en segundos
        """
        pass
    
    def draw(self):
        """Dibuja el estado en pantalla."""
        pass
    
    def enter(self):
        """Llamado al entrar en este estado."""
        pass
    
    def exit(self):
        """Llamado al salir de este estado."""
        pass


# MENU STATE

class MenuState(State):
    """Estado del menu principal - estilo retro Bomberman NES."""

    C_BG       = (20,  20,  30)
    C_SHADOW   = (120, 20,  0)
    C_SELECT   = (255, 200, 0)
    C_NORMAL   = (200, 200, 200)
    C_DISABLED = (70,  70,  70)
    C_HINT     = (90,  90,  110)
    C_CURSOR   = (255, 80,  0)

    def __init__(self, game):
        super().__init__(game)
        self.menu_options = [
            {"label": "JUGAR",        "enabled": True},
            {"label": "MULTIJUGADOR", "enabled": False},
            {"label": "OPCIONES",     "enabled": False},
            {"label": "SALIR",        "enabled": True},
        ]
        self.selected_index = 0
        self.title_pulse    = 0.0
        self.cursor_blink   = 0.0
        self.bg_offset      = 0.0

    def enter(self):
        print("Entrando al MENU")
        self.game.audio.play_music('menu')
        self._skip_to_enabled(1)

    def _skip_to_enabled(self, direction=1):
        for _ in range(len(self.menu_options)):
            if self.menu_options[self.selected_index]["enabled"]:
                break
            self.selected_index = (self.selected_index + direction) % len(self.menu_options)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == Controls.MENU_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.menu_options)
                    self._skip_to_enabled(-1)
                elif event.key == Controls.MENU_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.menu_options)
                    self._skip_to_enabled(1)
                elif event.key == Controls.MENU_SELECT:
                    self._select_option()
                    self.game.audio.play_sfx('menu_select')

    def _select_option(self):
        opt = self.menu_options[self.selected_index]
        if not opt["enabled"]:
            return
        label = opt["label"]
        if label == "JUGAR":
            self.game.num_players = 1
            self.game.change_state(GameStates.DIFFICULTY_SELECT)
        elif label == "SALIR":
            self.game.quit()

    def update(self, dt):
        self.title_pulse  += dt * 1.8
        self.cursor_blink += dt * 4.0
        self.bg_offset    += dt * 0.35

    def _draw_bg(self):
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        self.screen.fill(self.C_BG)
        tile   = 40
        offset = int(self.bg_offset * tile) % tile
        for gy in range(-1, H // tile + 2):
            for gx in range(-1, W // tile + 2):
                if (gx + gy) % 2 == 0:
                    s = pygame.Surface((tile, tile), pygame.SRCALPHA)
                    s.fill((255, 255, 255, 7))
                    self.screen.blit(s, (gx*tile - offset, gy*tile - offset))

    def draw(self):
        import math
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT

        self._draw_bg()
        pygame.draw.rect(self.screen, (55, 55, 75), (8, 8, W-16, H-16), 3)

        #  Titulo BOMBER / MAN 
        pulse = math.sin(self.title_pulse)
        so    = 5   # shadow offset

        # Renderizar a mano con superficie escalada para titulo MAS GRANDE
        # Usamos font_large * 2 escalando la superficie
        def draw_big_title(text, x, y, color, shadow_col):
            surf = self.font_large.render(text, True, shadow_col)
            # Escalar 1.8x para hacerlo mas grande
            w2 = int(surf.get_width() * 1.8)
            h2 = int(surf.get_height() * 1.8)
            big = pygame.transform.scale(surf, (w2, h2))
            self.screen.blit(big, (x - w2//2 + so, y - h2//2 + so))
            surf2 = self.font_large.render(text, True, color)
            big2  = pygame.transform.scale(surf2, (w2, h2))
            self.screen.blit(big2, (x - w2//2, y - h2//2))

        r1 = int(255)
        g1 = int(55 + 35 * pulse)
        draw_big_title("BOMBER", W//2, 95, (r1, g1, 25), self.C_SHADOW)

        r2 = int(255)
        g2 = int(195 + 30 * pulse)
        draw_big_title("MAN", W//2, 148, (r2, g2, 0), self.C_SHADOW)

        # Linea decorativa
        line_y = 183
        pygame.draw.line(self.screen, (100, 55, 0),  (W//2-200, line_y),   (W//2+200, line_y),   3)
        pygame.draw.line(self.screen, (220, 140, 0), (W//2-175, line_y+4), (W//2+175, line_y+4), 1)

        #  Opciones 
        # Medir el ancho maximo de las opciones para el recuadro
        max_label_w = 0
        for opt in self.menu_options:
            if opt["enabled"]:
                tw = self.font.size(opt["label"])[0]
                if tw > max_label_w:
                    max_label_w = tw

        # Recuadro se adapta al texto mas ancho + padding
        box_pad_x = 36   # padding horizontal del recuadro
        box_pad_y = 8    # padding vertical
        box_w     = max_label_w + box_pad_x * 2
        box_h     = self.font.get_height() + box_pad_y * 2

        start_y = 240
        spacing = 58

        cursor_on = math.sin(self.cursor_blink) > 0

        for i, opt in enumerate(self.menu_options):
            label   = opt["label"]
            enabled = opt["enabled"]
            is_sel  = (i == self.selected_index)
            # Centro vertical del texto en esta fila
            cy_text = start_y + i * spacing

            if not enabled:
                draw_text(self.screen, label,
                          (W//2, cy_text), self.font,
                          self.C_DISABLED, align='center')
                soon_surf = self.font_small.render("(PRONTO)", True, (55, 55, 55))
                self.screen.blit(soon_surf,
                    (W//2 - soon_surf.get_width()//2,
                     cy_text + self.font.get_height() + 2))
                continue

            if is_sel:
                # Recuadro centrado sobre la letra
                box_x = W//2 - box_w//2
                box_y = cy_text - box_pad_y
                # Fondo semitransparente
                bg_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                bg_s.fill((255, 160, 0, 38))
                self.screen.blit(bg_s, (box_x, box_y))
                # Borde naranja
                pygame.draw.rect(self.screen, (210, 125, 0),
                                 (box_x, box_y, box_w, box_h), 2)
                # Cursor parpadeante a la izquierda del recuadro
                if cursor_on:
                    draw_text(self.screen, ">",
                              (box_x - 10, cy_text),
                              self.font, self.C_CURSOR, align='right')
                # Texto centrado
                draw_text(self.screen, label,
                          (W//2, cy_text), self.font,
                          self.C_SELECT, align='center', shadow=True)
            else:
                draw_text(self.screen, label,
                          (W//2, cy_text), self.font,
                          self.C_NORMAL, align='center')

        #  Hint inferior 
        draw_text(self.screen, "FLECHAS: MOVER    ENTER: OK",
                  (W//2, H - 38), self.font_small, self.C_HINT, align='center')
        draw_text(self.screen, "BY ALEGO",
                  (W//2, H - 20), self.font_small, (45, 45, 65), align='center')


# PLAYING STATE

class PlayingState(State):
    """
    Estado de gameplay activo con nivel en curso.
    
    Este estado delega toda la lógica del nivel a GameLevelManager.
    Solo maneja pausa (ESC) y transiciones a GAMEOVER/VICTORY.
    
    Attributes:
        level (GameLevelManager): Gestor del nivel actual. None antes de enter().
    
    Notas:
        Al pausar, el nivel permanece en memoria y se resume al regresar.
        Al llegar a GAMEOVER o VICTORY, el nivel se destruye en exit().
    """
    
    def __init__(self, game):
        super().__init__(game)
        self.level_manager = None  # Se inicializa en enter()
    
    def enter(self):
        """Inicializa o reinicia el nivel."""
        print("Entrando a PLAYING")

        from game_level import LevelManager
        self.level_manager = LevelManager(self.game)
        # Número de jugadores elegido en el menú (default 1)
        self.level_manager.num_players = getattr(self.game, 'num_players', 1)
        self.level_manager.load_level(1)
    
    def exit(self):
        """Limpia recursos al salir."""
        if self.level_manager:
            self.level_manager.cleanup()
        print("Saliendo de PLAYING")
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == Controls.PAUSE:
                    self.game.change_state(GameStates.PAUSED)
                
                elif event.key == Controls.RESET:
                    # Reiniciar nivel
                    self.exit()
                    self.enter()
        
        # Pasar eventos al level manager
        if self.level_manager:
            self.level_manager.handle_events(events)
    
    def update(self, dt):
        if self.level_manager:
            self.level_manager.update(dt)
            
            # Verificar condiciones de victoria/derrota
            if self.level_manager.check_gameover():
                self.game.change_state(GameStates.GAMEOVER)
            elif self.level_manager.check_victory():
                self.game.change_state(GameStates.VICTORY)
    
    def draw(self):
        if self.level_manager:
            self.level_manager.draw(self.screen)


# PAUSED STATE

class PausedState(State):
    """Estado de pausa."""
    
    def __init__(self, game):
        super().__init__(game)
        self.menu_options = [
            "CONTINUAR",
            "REINICIAR",
            "MENÚ PRINCIPAL"
        ]
        self.selected_index = 0
        
        # Captura de pantalla del juego pausado
        self.game_screenshot = None
    
    def enter(self):
        print("Juego pausado")
        self.game.audio.pause_music()
        # Capturar pantalla actual
        self.game_screenshot = self.screen.copy()
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == Controls.PAUSE:
                    # Despausar
                    self.game.change_state(GameStates.PLAYING)
                
                elif event.key == Controls.MENU_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.menu_options)
                
                elif event.key == Controls.MENU_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.menu_options)
                
                elif event.key == Controls.MENU_SELECT:
                    self._select_option()
    
    def _select_option(self):
        option = self.menu_options[self.selected_index]
        
        if option == "CONTINUAR":
            self.game.audio.resume_music()
            self.game.change_state(GameStates.PLAYING)
        elif option == "REINICIAR":
            # Reiniciar nivel
            playing_state = self.game.states.get(GameStates.PLAYING)
            if playing_state:
                playing_state.exit()
                playing_state.enter()
            self.game.change_state(GameStates.PLAYING)
        elif option == "MENÚ PRINCIPAL":
            self.game.change_state(GameStates.MENU)
    
    def draw(self):
        # Dibujar juego detrás (oscurecido)
        if self.game_screenshot:
            self.screen.blit(self.game_screenshot, (0, 0))
        
        # Overlay semi-transparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Título "PAUSA"
        draw_text(
            self.screen, "PAUSA",
            (WINDOW_WIDTH // 2, 150),
            self.font_large,
            Colors.INVINCIBLE_GOLD,
            align='center',
            shadow=True
        )
        
        # Opciones
        start_y = 300
        spacing = 60
        
        for i, option in enumerate(self.menu_options):
            y = start_y + i * spacing
            
            if i == self.selected_index:
                color = Colors.INVINCIBLE_GOLD
                prefix = "▶ "
            else:
                color = Colors.WHITE
                prefix = "  "
            
            draw_text(
                self.screen,
                prefix + option,
                (WINDOW_WIDTH // 2, y),
                self.font,
                color,
                align='center',
                shadow=(i == self.selected_index)
            )
        
        # Controles
        controls = ": Navegar  |  ENTER: Seleccionar  |  ESC: Continuar"
        draw_text(
            self.screen, controls,
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),
            self.font_small,
            Colors.DEBUG_TEXT,
            align='center'
        )


# GAMEOVER STATE

class GameOverState(State):
    """Estado de game over (derrota)."""
    
    def __init__(self, game):
        super().__init__(game)
        self.timer = 0.0
        self.show_options = False
        self.selected_index = 0
        self.menu_options = ["REINTENTAR", "MENÚ PRINCIPAL"]
    
    def enter(self):
        self.timer = 0.0
        self.show_options = False
        self.game.audio.stop_music()
        self.game.audio.play_music('gameover', loops=0)
    
    def handle_events(self, events):
        if not self.show_options:
            # Esperar antes de mostrar opciones
            return
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == Controls.MENU_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.menu_options)
                
                elif event.key == Controls.MENU_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.menu_options)
                
                elif event.key == Controls.MENU_SELECT:
                    self._select_option()
    
    def _select_option(self):
        option = self.menu_options[self.selected_index]
        
        if option == "REINTENTAR":
            self.game.change_state(GameStates.PLAYING)
        elif option == "MENÚ PRINCIPAL":
            self.game.change_state(GameStates.MENU)
    
    def update(self, dt):
        self.timer += dt
        
        # Mostrar opciones después de 2 segundos
        if self.timer > 2.0:
            self.show_options = True
    
    def draw(self):
        # Fondo oscuro
        self.screen.fill(Colors.BLACK)
        
        # "GAME OVER" con efecto pulsante
        import math
        pulse = abs(math.sin(self.timer * 2))
        alpha = int(255 * (0.7 + pulse * 0.3))
        
        draw_text(
            self.screen, "GAME OVER",
            (WINDOW_WIDTH // 2, 200),
            self.font_large,
            (255, 50, 50, alpha) if isinstance((255, 50, 50, alpha), tuple) else (255, 50, 50),
            align='center',
            shadow=True
        )
        
        # Opciones (si ya pasó el tiempo)
        if self.show_options:
            start_y = 350
            spacing = 60
            
            for i, option in enumerate(self.menu_options):
                y = start_y + i * spacing
                
                if i == self.selected_index:
                    color = Colors.INVINCIBLE_GOLD
                    prefix = "▶ "
                else:
                    color = Colors.WHITE
                    prefix = "  "
                
                draw_text(
                    self.screen,
                    prefix + option,
                    (WINDOW_WIDTH // 2, y),
                    self.font,
                    color,
                    align='center'
                )


# VICTORY STATE

class VictoryState(State):
    """Estado de victoria."""
    
    def __init__(self, game):
        super().__init__(game)
        self.timer = 0.0
        self.fireworks = []
    
    def enter(self):
        self.timer = 0.0
        self.game.audio.stop_music()
        self.game.audio.play_music('level_complete', loops=0)
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (Controls.MENU_SELECT, Controls.PAUSE):
                    # Avanzar al siguiente nivel o volver al menú
                    self.game.change_state(GameStates.MENU)
    
    def update(self, dt):
        self.timer += dt
        # TODO: Actualizar animación de fuegos artificiales
    
    def draw(self):
        # Fondo
        self.screen.fill(Colors.BACKGROUND)
        
        # "¡VICTORIA!"
        draw_text(
            self.screen, "¡VICTORIA!",
            (WINDOW_WIDTH // 2, 200),
            self.font_large,
            Colors.INVINCIBLE_GOLD,
            align='center',
            shadow=True
        )
        
        # Mensaje
        másg = "Presiona ENTER para continuar"
        draw_text(
            self.screen, másg,
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100),
            self.font,
            Colors.WHITE,
            align='center'
        )


# DIFFICULTY SELECT STATE

class DifficultySelectState(State):
    """Seleccion de dificultad - estilo retro."""

    DIFF_COLORS = {
        'FACIL':   (80,  220, 80),
        'NORMAL':  (255, 200, 0),
        'DIFICIL': (255, 60,  30),
    }

    def __init__(self, game):
        super().__init__(game)
        self.difficulties   = DifficultyConfig.DIFFICULTIES
        self.selected_index = 1
        self.pulse_timer    = 0.0

    def enter(self):
        print("Seleccion de dificultad")
        if hasattr(self.game, 'audio'):
            self.game.audio.play_music('menu')

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == Controls.MENU_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.difficulties)
                elif event.key == Controls.MENU_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.difficulties)
                elif event.key == Controls.MENU_SELECT:
                    self._select_difficulty()
                elif event.key == Controls.PAUSE:
                    self.game.change_state(GameStates.MENU)

    def _select_difficulty(self):
        difficulty = self.difficulties[self.selected_index]
        self.game.difficulty = difficulty
        print(f"Dificultad: {difficulty}")
        self.game.change_state(GameStates.PLAYER_SELECT)

    def update(self, dt):
        self.pulse_timer += dt

    def draw(self):
        import math
        W, H  = WINDOW_WIDTH, WINDOW_HEIGHT
        t     = self.pulse_timer

        self.screen.fill((20, 20, 30))
        pygame.draw.rect(self.screen, (55, 55, 75), (8, 8, W-16, H-16), 3)

        # Titulo
        so = 4
        tsurf = self.font_large.render("DIFICULTAD", True, (120, 20, 0))
        tw2   = int(tsurf.get_width() * 1.5)
        th2   = int(tsurf.get_height() * 1.5)
        tbig  = pygame.transform.scale(tsurf, (tw2, th2))
        self.screen.blit(tbig, (W//2 - tw2//2 + so, 52 + so))
        tsurf2 = self.font_large.render("DIFICULTAD", True, (255, 180, 0))
        tbig2  = pygame.transform.scale(tsurf2, (tw2, th2))
        self.screen.blit(tbig2, (W//2 - tw2//2, 52))

        ly = 52 + th2 + 8
        pygame.draw.line(self.screen, (200, 120, 0), (W//2-180, ly), (W//2+180, ly), 2)

        # Opciones
        start_y = ly + 30
        # Altura de cada bloque: seleccionado es mas alto
        row_h_normal = 62
        row_h_sel    = 110

        # Calcular posicion y de cada opcion
        y_positions = []
        cy = start_y
        for i in range(len(self.difficulties)):
            y_positions.append(cy)
            cy += row_h_sel if i == self.selected_index else row_h_normal

        for i, difficulty in enumerate(self.difficulties):
            y      = y_positions[i]
            is_sel = (i == self.selected_index)
            config = DifficultyConfig.get_config(difficulty)
            base_col = self.DIFF_COLORS.get(difficulty, (200, 200, 200))

            if is_sel:
                pulse  = math.sin(t * 4) * 0.5 + 0.5
                pw, ph = 520, row_h_sel - 8
                px     = W//2 - pw//2
                # Fondo panel
                bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
                bg.fill((base_col[0]//6, base_col[1]//6, base_col[2]//6, 210))
                self.screen.blit(bg, (px, y))
                # Borde pulsante
                bc = tuple(int(c*(0.55 + 0.45*pulse)) for c in base_col)
                pygame.draw.rect(self.screen, bc, (px, y, pw, ph), 2)
                pygame.draw.rect(self.screen, (255, 255, 255, 50), (px+3, y+3, pw-6, ph-6), 1)
                # Cursor
                if int(t * 4) % 2 == 0:
                    draw_text(self.screen, ">", (px + 16, y + 12),
                              self.font, (255, 80, 0), align='left')
                # Nombre - escalar para hacerlo mas grande
                nsurf = self.font_large.render(difficulty, True, base_col)
                nw2   = int(nsurf.get_width() * 1.3)
                nh2   = int(nsurf.get_height() * 1.3)
                nbig  = pygame.transform.scale(nsurf, (nw2, nh2))
                self.screen.blit(nbig, (W//2 - nw2//2, y + 6))
                # Descripcion
                draw_text(self.screen, config['description'],
                          (W//2, y + nh2 + 10), self.font_small,
                          (200, 200, 200), align='center')
                # Stats
                s1 = f"VIDAS: {config['player_lives']}   ENEMIGOS: {int(config['enemy_count_multiplier']*100)}%"
                s2 = f"VEL: {int(config['enemy_speed_multiplier']*100)}%   POWERUPS: {int(config['powerup_drop_chance']*100)}%"
                draw_text(self.screen, s1, (W//2, y + nh2 + 28), self.font_small, (155, 155, 175), align='center')
                draw_text(self.screen, s2, (W//2, y + nh2 + 44), self.font_small, (155, 155, 175), align='center')
            else:
                # No seleccionado: solo nombre pequeno en gris
                nsurf = self.font.render(difficulty, True, (90, 90, 90))
                self.screen.blit(nsurf, (W//2 - nsurf.get_width()//2, y + 8))
                dsurf = self.font_small.render(config['description'], True, (60, 60, 60))
                self.screen.blit(dsurf, (W//2 - dsurf.get_width()//2, y + 32))

        draw_text(self.screen, "FLECHAS: MOVER    ENTER: OK    ESC: VOLVER",
                  (W//2, H - 22), self.font_small, (80, 80, 100), align='center')


class PlayerSelectState(State):
    """
    Pantalla de selección de número de jugadores.
    Se accede desde MENU  "MULTIJUGADOR" o directamente con tecla 2.
    """

    def __init__(self, game):
        super().__init__(game)
        self.options = [
            {"label": "1 JUGADOR",   "players": 1,
             "desc": "Flechas + Espacio"},
            {"label": "2 JUGADORES", "players": 2,
             "desc": "P1: Flechas + Espacio  |  P2: WASD + F"},
             {"label": "2 JUGADORES", "players": 3,
             "desc": "P1: Flechas + Espacio  |  P2: WASD + F  |  P3: IJKL + U"},
#             {"label": "2 JUGADORES", "players": 4,
#             "desc": "P1: Flechas + Espacio  |  P2: WASD + F  |  P3: IJKL + U  |  P4: 8456 + 0"},
        ]
        self.selected = 0
        self.pulse = 0.0

    def enter(self):
        print("Selección de jugadores")
        self.selected = 0
        self.game.audio.play_music('menu')

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (Controls.MENU_UP, pygame.K_LEFT):
                    self.selected = (self.selected - 1) % len(self.options)
                    self.game.audio.play_sfx('menu_select')
                elif event.key in (Controls.MENU_DOWN, pygame.K_RIGHT):
                    self.selected = (self.selected + 1) % len(self.options)
                    self.game.audio.play_sfx('menu_select')
                elif event.key == Controls.MENU_SELECT:
                    self._confirm()
                    self.game.audio.play_sfx('menu_select')
                elif event.key == Controls.PAUSE:
                    self.game.change_state(GameStates.MENU)
                elif event.key == pygame.K_1:
                    self.game.num_players = 1
                    self.game.change_state(GameStates.PLAYING)
                elif event.key == pygame.K_2:
                    self.game.num_players = 2
                    self.game.change_state(GameStates.PLAYING)

    def _confirm(self):
        self.game.num_players = self.options[self.selected]["players"]
        self.game.change_state(GameStates.PLAYING)

    def update(self, dt):
        self.pulse += dt * 3

    def draw(self):
        import math
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        t    = self.pulse

        self.screen.fill((20, 20, 30))
        pygame.draw.rect(self.screen, (55, 55, 75), (8, 8, W-16, H-16), 3)

        # Titulo
        so    = 4
        tsurf = self.font_large.render("JUGADORES", True, (120, 20, 0))
        tw2   = int(tsurf.get_width() * 1.5)
        th2   = int(tsurf.get_height() * 1.5)
        tbig  = pygame.transform.scale(tsurf, (tw2, th2))
        self.screen.blit(tbig, (W//2 - tw2//2 + so, 52 + so))
        tsurf2 = self.font_large.render("JUGADORES", True, (255, 180, 0))
        tbig2  = pygame.transform.scale(tsurf2, (tw2, th2))
        self.screen.blit(tbig2, (W//2 - tw2//2, 52))
        ly = 52 + th2 + 8
        pygame.draw.line(self.screen, (200, 120, 0), (W//2-160, ly), (W//2+160, ly), 2)

        # Tarjetas
        card_w, card_h = 280, 210
        gap    = 60
        total  = len(self.options) * card_w + (len(self.options)-1) * gap
        sx     = (W - total) // 2
        cy_base = H//2 - card_h//2 + 30

        for i, opt in enumerate(self.options):
            cx     = sx + i * (card_w + gap)
            is_sel = (i == self.selected)
            pulse  = math.sin(t) * 0.5 + 0.5

            if is_sel:
                # Resplandor exterior
                gl = pygame.Surface((card_w+20, card_h+20), pygame.SRCALPHA)
                gl.fill((255, 160, 0, int(18 + 14*pulse)))
                self.screen.blit(gl, (cx-10, cy_base-10))
                pygame.draw.rect(self.screen, (30, 30, 48),
                                 (cx, cy_base, card_w, card_h))
                bw = int(3 + pulse * 1.5)
                bc = (255, int(155 + 45*pulse), 0)
                pygame.draw.rect(self.screen, bc,
                                 (cx, cy_base, card_w, card_h), bw)
                # Linea interior
                pygame.draw.rect(self.screen, (200, 200, 255, 50),
                                 (cx+5, cy_base+5, card_w-10, card_h-10), 1)
            else:
                pygame.draw.rect(self.screen, (22, 22, 32),
                                 (cx, cy_base, card_w, card_h))
                pygame.draw.rect(self.screen, (65, 65, 88),
                                 (cx, cy_base, card_w, card_h), 2)

            # Numero grande — escalado
            num_col  = (255, 200, 0) if is_sel else (75, 75, 75)
            nsurf    = self.font_large.render(str(opt["players"]), True, num_col)
            nw2, nh2 = int(nsurf.get_width()*2.0), int(nsurf.get_height()*2.0)
            nbig     = pygame.transform.scale(nsurf, (nw2, nh2))
            self.screen.blit(nbig, (cx + card_w//2 - nw2//2, cy_base + 28))

            # Etiqueta
            lbl_col = (255, 255, 255) if is_sel else (90, 90, 90)
            draw_text(self.screen, opt["label"],
                      (cx + card_w//2, cy_base + 28 + nh2 + 12),
                      self.font, lbl_col, align='center', shadow=is_sel)

            # Controles
            ctrl_col = (150, 150, 175) if is_sel else (55, 55, 55)
            draw_text(self.screen, opt["desc"],
                      (cx + card_w//2, cy_base + 28 + nh2 + 38),
                      self.font_small, ctrl_col, align='center')

            # Indicador seleccionado
            if is_sel and int(t * 4) % 2 == 0:
                draw_text(self.screen, "< SELECCIONADO >",
                          (cx + card_w//2, cy_base - 22),
                          self.font_small, (255, 160, 0), align='center')

        draw_text(self.screen,
                  "FLECHAS: MOVER    ENTER: OK    ESC: VOLVER",
                  (W//2, H - 22), self.font_small, (80, 80, 100), align='center')


# STATE MANAGER (Opcional, para organización extra)

class StateManager:
    """
    Gestor centralizado de transiciones entre estados.
    
    Mantiene referencia al estado actual y orquesta cambios llamando
    automáticamente exit() del estado saliente y enter() del entrante.
    Delega eventos y actualizaciones al estado activo.
    
    Attributes:
        game: Referencia a Game.
        current_state (State): Estado actualmente activo.
    
    Notas:
        Los estados se registran con add_state() antes de poder
        usarse en change_state(). El cambio es instantáneo (sin fade).
    """
    
    def __init__(self, game):
        self.game = game
        self.states = {}
        self.current_state = None
        self.previous_state = None
    
    def add_state(self, name, state):
        """Agrega un estado al manager."""
        self.states[name] = state
    
    def change_state(self, name):
        """Cambia al estado especificado."""
        if name not in self.states:
            print(f"  Estado '{name}' no existe")
            return
        
        # Salir del estado actual
        if self.current_state:
            self.current_state.exit()
            self.previous_state = self.current_state
        
        # Entrar al nuevo estado
        self.current_state = self.states[name]
        self.current_state.enter()
        
        print(f"Estado cambiado: {name}")
    
    def handle_events(self, events):
        """Delega eventos al estado actual."""
        if self.current_state:
            self.current_state.handle_events(events)
    
    def update(self, dt):
        """Actualiza el estado actual."""
        if self.current_state:
            self.current_state.update(dt)
    
    def draw(self):
        """Dibuja el estado actual."""
        if self.current_state:
            self.current_state.draw()