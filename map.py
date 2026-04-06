"""
Sistema de generación y gestión del laberinto.

Este módulo implementa la clase Maze que genera y gestiona el laberinto
del juego. Usa generación procedural con patrón de tablero de ajedrez
para garantizar navegabilidad.

Tipos de Bloques:
    - EMPTY (0): Espacio vacío navegable
    - IRONBRICK (1): Muro indestructible de borde
    - BRICK (2): Ladrillo destructible (drop de powerup)
    - DOOR (3): Puerta de salida (abre con todas las llaves)

Algoritmo de Generación:
    1. Llenar bordes con IRONBRICK
    2. Patrón de tablero de ajedrez interno
    3. Colocar BRICK en celdas vacías (70% probabilidad)
    4. Limpiar áreas de spawn de jugadores (3x3)
    5. Colocar puerta en posición fija
    6. Flood fill para verificar navegabilidad

Clases Exportadas:
    - Maze: Laberinto con generación procedural

Uso Típico:
    maze = Maze(rows=15, cols=19, cell_size=32)
    
    # Verificar colisión
    rect = pygame.Rect(x, y, width, height)
    if maze.check_collision_with_blocks(rect):
        # Bloqueado
    
    # Destruir ladrillo
    destroyed = maze.destroy_brick_at_pixel(x, y)

Notas:
    El algoritmo garantiza que siempre hay camino desde spawn del
    jugador hasta la puerta. Los bloques en posiciones impares (tablero
    de ajedrez) son siempre IRONBRICK para evitar mapa completamente vacío.
"""


import pygame
import random
from settings import (
    CELL_SIZE, MAP_ROWS, MAP_COLS, WINDOW_WIDTH, WINDOW_HEIGHT,
    Colors
)
from utils import load_image


# CAMERA  (1 jugador, sin zoom)

class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.width      = width
        self.height     = height
        self.map_width  = map_width
        self.map_height = map_height
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0

    def update(self, players_or_cx, dt_or_cy=None):
        if isinstance(players_or_cx, (int, float)):
            cx, cy = players_or_cx, dt_or_cy
        else:
            players = players_or_cx
            alive = [p for p in players
                     if not getattr(p, 'dead', False)
                     and not getattr(p, 'finish', False)]
            if not alive:
                alive = players
            p = alive[0]
            cx = p.x + p.width  // 2
            cy = p.y + p.height // 2
        self.x = max(0, min(cx - self.width  // 2,
                            self.map_width  - self.width))
        self.y = max(0, min(cy - self.height // 2,
                            self.map_height - self.height))

    def apply(self, world_x, world_y):
        return (world_x - self.x, world_y - self.y)


# _VIEWPORT  (helper interno de SplitCamera)

class _Viewport:
    def __init__(self, screen_rect, map_width, map_height):
        self.screen_rect = screen_rect
        self.map_width   = map_width
        self.map_height  = map_height
        self.x    = 0.0
        self.y    = 0.0
        self.zoom = 1.0

    @property
    def width(self):   return self.map_width
    @property
    def height(self):  return self.map_height

    def follow(self, player):
        vw = self.screen_rect.width
        vh = self.screen_rect.height
        cx = player.x + player.width  // 2
        cy = player.y + player.height // 2
        self.x = max(0, min(cx - vw // 2, self.map_width  - vw))
        self.y = max(0, min(cy - vh // 2, self.map_height - vh))

    def follow_diagonal(self, player, target_sx, target_sy):
        """
        Sigue al jugador posicionando su sprite en (target_sx, target_sy)
        de pantalla en lugar del centro. Así queda en el interior de su
        triángulo y alejado de la línea diagonal.

        Derivación:
            screen_x = cx - cam_x  =>  cam_x = cx - target_sx
            screen_y = cy - cam_y  =>  cam_y = cy - target_sy

        El clamp final respeta los límites del mapa.

        Args:
            target_sx: posición X deseada del jugador en pantalla (px)
            target_sy: posición Y deseada del jugador en pantalla (px)
        """
        vw = self.screen_rect.width
        vh = self.screen_rect.height
        cx = player.x + player.width  // 2
        cy = player.y + player.height // 2
        self.x = max(0, min(cx - target_sx, self.map_width  - vw))
        self.y = max(0, min(cy - target_sy, self.map_height - vh))

    def apply(self, world_x, world_y):
        return (world_x - self.x, world_y - self.y)


# SPLIT CAMERA - CON DIAGONAL CELDA POR CELDA

class SplitCamera:
    """
    Cámara con división diagonal CORRECTA usando cálculo celda por celda.
    
    Basado en la fórmula del PDF:
    - MAIN diagonal (↘): X = (Y / height) × width
    - ANTI diagonal (↙): X = width - (Y / height) × width
    """

    DIVIDER_COLOR = (100, 100, 100)   # azul brillante, visible sobre cualquier fondo
    DIVIDER_WIDTH = 8               # grosor en todos los modos
    SPLIT_THRESHOLD_FACTOR = 0.6

    def __init__(self, screen_w, screen_h, map_width, map_height):
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.map_width  = map_width
        self.map_height = map_height
        self.zoom = 1.0

        self.split_mode = 'merged'
        self._prev_mode = 'merged'
        
        half_h = screen_h // 2
        half_w = screen_w // 2
        
        # Horizontal split
        self._vp_horizontal = [
            _Viewport(pygame.Rect(0, 0,      screen_w, half_h), map_width, map_height),
            _Viewport(pygame.Rect(0, half_h, screen_w, half_h), map_width, map_height),
        ]
        
        # Vertical split
        self._vp_vertical = [
            _Viewport(pygame.Rect(0,      0, half_w, screen_h), map_width, map_height),
            _Viewport(pygame.Rect(half_w, 0, half_w, screen_h), map_width, map_height),
        ]
        
        # Diagonal split - ambos viewports usan pantalla completa
        self._vp_diagonal = [
            _Viewport(pygame.Rect(0, 0, screen_w, screen_h), map_width, map_height),
            _Viewport(pygame.Rect(0, 0, screen_w, screen_h), map_width, map_height),
        ]
        
        self._diagonal_type = 'main'  # 'main' (↘) o 'anti' (↙)
        
        # Merged
        self._vp_merged = _Viewport(
            pygame.Rect(0, 0, screen_w, screen_h), map_width, map_height
        )
        
        self._players = []

    def update(self, players, dt=0.016):
        """Actualiza la cámara según la posición de los jugadores."""
        self._players = list(players)
        alive = [p for p in players
                 if not getattr(p, 'dead', False)
                 and not getattr(p, 'finish', False)]
        
        if len(alive) < 2:
            p = alive[0] if alive else players[0]
            self._vp_merged.follow(p)
            self._set_mode('merged')
            return

        p0, p1 = alive[0], alive[1]
        
        x0 = p0.x + p0.width  // 2
        y0 = p0.y + p0.height // 2
        x1 = p1.x + p1.width  // 2
        y1 = p1.y + p1.height // 2
        
        dist_x = abs(x1 - x0)
        dist_y = abs(y1 - y0)
        
        threshold_x = self.screen_w * self.SPLIT_THRESHOLD_FACTOR
        threshold_y = self.screen_h * self.SPLIT_THRESHOLD_FACTOR
        
        new_mode = self._determine_split_mode(dist_x, dist_y, threshold_x, threshold_y)
        self._set_mode(new_mode)
        
        if self.split_mode == 'merged':
            self._update_merged(p0, p1, x0, y0, x1, y1)
        elif self.split_mode == 'horizontal':
            self._update_horizontal(p0, p1)
        elif self.split_mode == 'vertical':
            self._update_vertical(p0, p1)
        elif self.split_mode == 'diagonal':
            self._update_diagonal(p0, p1, x0, y0, x1, y1)

    def _determine_split_mode(self, dist_x, dist_y, threshold_x, threshold_y):
        if dist_x < threshold_x and dist_y < threshold_y:
            return 'merged'
        elif dist_y > threshold_y and dist_x < threshold_x:
            return 'horizontal'
        elif dist_x > threshold_x and dist_y < threshold_y:
            return 'vertical'
        else:
            return 'diagonal'

    def _set_mode(self, new_mode):
        if new_mode != self.split_mode:
            self._prev_mode = self.split_mode
            self.split_mode = new_mode

    def _update_merged(self, p0, p1, x0, y0, x1, y1):
        center_x = (x0 + x1) // 2
        center_y = (y0 + y1) // 2
        vw = self._vp_merged.screen_rect.width
        vh = self._vp_merged.screen_rect.height
        self._vp_merged.x = max(0, min(center_x - vw // 2, self.map_width - vw))
        self._vp_merged.y = max(0, min(center_y - vh // 2, self.map_height - vh))

    def _update_horizontal(self, p0, p1):
        if p0.y < p1.y:
            top_player, bottom_player = p0, p1
        else:
            top_player, bottom_player = p1, p0
        self._vp_horizontal[0].follow(top_player)
        self._vp_horizontal[1].follow(bottom_player)

    def _update_vertical(self, p0, p1):
        if p0.x < p1.x:
            left_player, right_player = p0, p1
        else:
            left_player, right_player = p1, p0
        self._vp_vertical[0].follow(left_player)
        self._vp_vertical[1].follow(right_player)

    def _update_diagonal(self, p0, p1, x0, y0, x1, y1):
        """
        Asigna cada jugador a su viewport y llama a follow_diagonal()
        con el centro geométrico de su triángulo visible en pantalla.

        Según should_draw_at_position (valores verificados):
          diagonal_type='anti' (↘ de arriba-izq a abajo-der):
            vp[0] = lado IZQUIERDO  de la diagonal  target (sw//4,  sh//2)
            vp[1] = lado DERECHO    de la diagonal  target (sw*3//4, sh//2)
          diagonal_type='main' (↙ de arriba-der a abajo-izq):
            vp[0] = lado DERECHO    de la diagonal  target (sw*3//4, sh//2)
            vp[1] = lado IZQUIERDO  de la diagonal  target (sw//4,  sh//2)

        El jugador del lado izquierdo siempre va a vp del lado izquierdo, etc.
        """
        dx = x1 - x0
        dy = y1 - y0

        sw, sh = self.screen_w, self.screen_h

        # Centro geométrico de cada mitad triangular
        # El triángulo izquierdo/derecho tiene su centroide a sw//4 o sw*3//4
        # Verticalmente ambos van al centro sh//2
        T_LEFT  = (sw // 4,     sh // 2)   # centro del triángulo izquierdo
        T_RIGHT = (sw * 3 // 4, sh // 2)   # centro del triángulo derecho

        if dx * dy >= 0:
            # Diagonal ↘    diagonal_type = 'anti'
            # vp[0] = izquierda, vp[1] = derecha
            self._diagonal_type = 'anti'
            # El jugador más a la izquierda en mundo va al vp izquierdo
            if x0 <= x1:
                self._vp_diagonal[0].follow_diagonal(p0, *T_LEFT)
                self._vp_diagonal[1].follow_diagonal(p1, *T_RIGHT)
            else:
                self._vp_diagonal[0].follow_diagonal(p1, *T_LEFT)
                self._vp_diagonal[1].follow_diagonal(p0, *T_RIGHT)
        else:
            # Diagonal ↙    diagonal_type = 'main'
            # vp[0] = derecha, vp[1] = izquierda
            self._diagonal_type = 'main'
            # El jugador más a la derecha en mundo va al vp derecho (vp[0])
            if x0 >= x1:
                self._vp_diagonal[0].follow_diagonal(p0, *T_RIGHT)
                self._vp_diagonal[1].follow_diagonal(p1, *T_LEFT)
            else:
                self._vp_diagonal[0].follow_diagonal(p1, *T_RIGHT)
                self._vp_diagonal[1].follow_diagonal(p0, *T_LEFT)


    def get_diagonal_clip_x(self, screen_y):
        """
        Calcula dónde cruza la diagonal en una fila Y de la pantalla.
        
        Fórmulas INVERTIDAS para compensar etiquetas invertidas:
        - MAIN (↘): X = width - (Y / height) × width   De (w,0) a (0,h)
        - ANTI (↙): X = (Y / height) × width   De (0,0) a (w,h)
        """
        if self._diagonal_type == 'anti':
            x_diagonal = int(self.screen_w - (screen_y / self.screen_h) * self.screen_w)
        else:
            x_diagonal = int((screen_y / self.screen_h) * self.screen_w)
        
        return x_diagonal

    def should_draw_at_position(self, screen_x, screen_y, viewport_index):
        """
        Determina si una celda debe dibujarse en el viewport dado.
        
        Args:
            screen_x, screen_y: Posición en pantalla
            viewport_index: 0 para viewport[0], 1 para viewport[1]
        
        Returns:
            bool: True si debe dibujarse
            
        Nota: Lógica INVERTIDA para compensar etiquetas invertidas.
        """
        if self.split_mode != 'diagonal':
            return True
        
        x_diagonal = self.get_diagonal_clip_x(screen_y)
        
        if self._diagonal_type == 'main':
            if viewport_index == 0:
                return screen_x >= x_diagonal
            else:
                return screen_x < x_diagonal
        else:  # 'main'
            if viewport_index == 0:
                return screen_x < x_diagonal   # INVERTIDO
            else:
                return screen_x >= x_diagonal  # INVERTIDO

    def iter_viewports(self, screen):
        """Itera sobre viewports activos."""
        if self.split_mode == 'merged':
            yield (screen, self._vp_merged, None)
        
        elif self.split_mode == 'horizontal':
            for vp in self._vp_horizontal:
                sr = vp.screen_rect
                sub = screen.subsurface(sr)
                yield (sub, vp, None)
        
        elif self.split_mode == 'vertical':
            for vp in self._vp_vertical:
                sr = vp.screen_rect
                sub = screen.subsurface(sr)
                yield (sub, vp, None)
        
        elif self.split_mode == 'diagonal':
            yield (screen, self._vp_diagonal[0], 'diagonal_p1')
            yield (screen, self._vp_diagonal[1], 'diagonal_p2')

    def draw_divider(self, screen):
        """Dibuja la línea divisoria visible en todos los modos."""
        if self.split_mode == 'merged':
            return

        color = self.DIVIDER_COLOR
        w_line = self.DIVIDER_WIDTH

        if self.split_mode == 'horizontal':
            y = self.screen_h // 2
            pygame.draw.line(screen, color,
                             (0, y), (self.screen_w, y), w_line)

        elif self.split_mode == 'vertical':
            x = self.screen_w // 2
            pygame.draw.line(screen, color,
                             (x, 0), (x, self.screen_h), w_line)

        elif self.split_mode == 'diagonal':
            w, h = self.screen_w, self.screen_h
            # Para diagonales, pygame.draw.line con width > 1 queda pixelado.
            # Dibujamos varias líneas paralelas ligeramente desplazadas
            # (desplazamiento perpendicular a la diagonal) para grosor uniforme.
            half = w_line // 2
            if self._diagonal_type == 'main':   # ↘  de (0,0) a (w,h)
                for d in range(-half, half + 1):
                    pygame.draw.line(screen, color,
                                     (d, 0), (w + d, h), 1)
            else:                               # ↙  de (w,0) a (0,h)
                for d in range(-half, half + 1):
                    pygame.draw.line(screen, color,
                                     (w + d, 0), (d, h), 1)

    def apply(self, world_x, world_y):
        if self.split_mode == 'merged':
            return self._vp_merged.apply(world_x, world_y)
        elif self.split_mode == 'horizontal':
            return self._vp_horizontal[0].apply(world_x, world_y)
        elif self.split_mode == 'vertical':
            return self._vp_vertical[0].apply(world_x, world_y)
        else:
            return self._vp_diagonal[0].apply(world_x, world_y)

    @property
    def x(self):
        if self.split_mode == 'merged':
            return self._vp_merged.x
        elif self.split_mode == 'horizontal':
            return self._vp_horizontal[0].x
        elif self.split_mode == 'vertical':
            return self._vp_vertical[0].x
        else:
            return self._vp_diagonal[0].x
    
    @property
    def y(self):
        if self.split_mode == 'merged':
            return self._vp_merged.y
        elif self.split_mode == 'horizontal':
            return self._vp_horizontal[0].y
        elif self.split_mode == 'vertical':
            return self._vp_vertical[0].y
        else:
            return self._vp_diagonal[0].y
    
    @property
    def width(self):
        return self.screen_w
    
    @property
    def height(self):
        return self.screen_h


# MAZE

class Maze:
    """Laberinto DFS clásico."""

    def __init__(self, rows, cols, cell_size, player_start_pos):
        self.rows      = rows
        self.cols      = cols
        self.cell_size = cell_size
        self.width     = cols * cell_size
        self.height    = rows * cell_size
        self.player_start_x = player_start_pos[0]
        self.player_start_y = player_start_pos[1]

        self.grid = [['ironbrick'] * cols for _ in range(rows)]

        self.tiles = {
            'ironbrick': load_image('ironbrick.png'),
            'brick':     load_image('brick.png'),
            'door':      load_image('door.png'),
            'empty':     None,
        }

        self.door_row = rows - 2
        self.door_col = cols - 2
        self.door_open = False
        self.num_players = 1

    def generate(self, num_players=1, brick_density=None):
        """
        Genera el laberinto.
        
        Args:
            num_players: Número de jugadores (afecta spawns y puerta)
            brick_density: Densidad de ladrillos (0.0-1.0). None usa el valor
                           por defecto de 0.18 definido en _place_bricks.
        """
        self.num_players = num_players
        self._generate_maze(num_players, brick_density=brick_density)
        self.door_row, self.door_col = self._door_cell(num_players)

    def _spawn_cells(self, num_players):
        """
        Retorna las celdas de spawn para cada jugador.
        Usa PlayerConfig.SPAWN_OFFSETS de settings.py
        
        Args:
            num_players: Número de jugadores (1-4)
        
        Returns:
            List[(row, col)]: Posiciones de spawn
        """
        from settings import PlayerConfig
        
        spawns = []
        for player_id in range(1, num_players + 1):
            # Obtener offset configurado (col, row)
            spawn_offset = PlayerConfig.SPAWN_OFFSETS.get(player_id, (1, 1))
            col, row = spawn_offset
            spawns.append((row, col))
        
        return spawns

    def _door_cell(self, num_players):
        if num_players <= 2:
            return (self.rows // 2, self.cols - 4)
        else:
            return (self.rows // 2, self.cols // 2)

    def _generate_maze(self, num_players, brick_density=None):
        self._dfs_carve(1, 1)
        door_r, door_c = self._door_cell(num_players)
        self._build_door_room(door_r, door_c, num_players)
        for sr, sc in self._spawn_cells(num_players):
            self._connect_spawn_to_maze(sr, sc)
        # Usar brick_density si se especificó, si no el default de 0.18
        density = brick_density if brick_density is not None else 0.18
        self._place_bricks(num_players, density=density)
        self._clear_spawn_areas(num_players)
        self._ensure_path_to_door(num_players)

    def _dfs_carve(self, r, c):
        self.grid[r][c] = 'empty'
        dirs = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        random.shuffle(dirs)

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1:
                if self.grid[nr][nc] == 'ironbrick':
                    wr, wc = r + dr // 2, c + dc // 2
                    self.grid[wr][wc] = 'empty'
                    self._dfs_carve(nr, nc)

    def _connect_spawn_to_maze(self, sr, sc):
        target_c = self.cols // 2
        target_r = self.rows // 2

        best_r, best_c = 1, 1
        best_d = 9999
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if self.grid[r][c] == 'empty':
                    d = abs(r - target_r) + abs(c - target_c)
                    if d < best_d:
                        best_d, best_r, best_c = d, r, c

        r = target_r
        step = 1 if best_r > r else -1
        while r != best_r:
            if 0 < r < self.rows - 1:
                self.grid[r][target_c] = 'empty'
            r += step
        if 0 < target_r < self.rows - 1 and 0 < target_c < self.cols - 1:
            self.grid[target_r][target_c] = 'empty'

        c = target_c
        step = 1 if best_c > c else -1
        while c != best_c:
            if 0 < c < self.cols - 1:
                self.grid[best_r][c] = 'empty'
            c += step

    def _build_door_room(self, door_r, door_c, num_players):
        if num_players <= 2:
            self._door_room_lateral(door_r, door_c, num_players)
        else:
            self._door_room_central(door_r, door_c)

    def _door_room_lateral(self, door_r, door_c, num_players):
        wall_col  = door_c - 3
        room_rows = range(door_r - 2, door_r + 3)

        for r in room_rows:
            for c in range(wall_col + 1, door_c + 1):
                if 0 < r < self.rows - 1 and 0 < c < self.cols - 1:
                    self.grid[r][c] = 'empty'

        for r in room_rows:
            if 0 < r < self.rows - 1 and 0 < wall_col < self.cols - 1:
                self.grid[r][wall_col] = 'ironbrick'

        if num_players == 1:
            self.grid[door_r][wall_col] = 'empty'
        else:
            for dr in [-1, 1]:
                r = door_r + dr
                if 0 < r < self.rows - 1:
                    self.grid[r][wall_col] = 'empty'

        self.grid[door_r][door_c] = 'door'

    def _door_room_central(self, door_r, door_c):
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = door_r + dr, door_c + dc
                if 0 < r < self.rows - 1 and 0 < c < self.cols - 1:
                    self.grid[r][c] = 'empty'

        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) == 2 or abs(dc) == 2:
                    r, c = door_r + dr, door_c + dc
                    if 0 < r < self.rows - 1 and 0 < c < self.cols - 1:
                        self.grid[r][c] = 'ironbrick'

        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            r, c = door_r + dr, door_c + dc
            if 0 < r < self.rows - 1 and 0 < c < self.cols - 1:
                self.grid[r][c] = 'empty'

        self.grid[door_r][door_c] = 'door'

    def _place_bricks(self, num_players=1, density=0.18):
        door_r, door_c = self._door_cell(num_players)
        protected = set()

        for sr, sc in self._spawn_cells(num_players):
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    protected.add((sr + dr, sc + dc))

        for dr in range(-3, 4):
            for dc in range(-4, 1):
                protected.add((door_r + dr, door_c + dc))

        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if (r, c) not in protected and self.grid[r][c] == 'empty':
                    if random.random() < density:
                        self.grid[r][c] = 'brick'

    def _clear_spawn_areas(self, num_players=1):
        for sr, sc in self._spawn_cells(num_players):
            is_right  = sc > self.cols // 2
            is_bottom = sr > self.rows // 2
            dc_dir = -1 if is_right  else 1
            dr_dir = -1 if is_bottom else 1

            if 0 < sr < self.rows - 1 and 0 < sc < self.cols - 1:
                self.grid[sr][sc] = 'empty'

            for step in [1, 2]:
                for dr, dc in [(0, dc_dir * step), (dr_dir * step, 0)]:
                    r, c = sr + dr, sc + dc
                    if 0 < r < self.rows - 1 and 0 < c < self.cols - 1:
                        if self.grid[r][c] == 'brick':
                            self.grid[r][c] = 'empty'


    def _ensure_path_to_door(self, num_players=1):
        """Garantiza camino desde cada spawn hasta la puerta usando Flood Fill."""
        door_r, door_c = self._door_cell(num_players)
        
        for spawn_idx, (sr, sc) in enumerate(self._spawn_cells(num_players)):
            attempts = 0
            max_attempts = 50
            
            while attempts < max_attempts:
                visited = self._flood_fill(sr, sc)
                
                if (door_r, door_c) in visited:
                    print(f"[MAP] Spawn {spawn_idx+1} conectado a puerta ")
                    break
                
                brick_removed = self._remove_blocking_brick(visited, door_r, door_c)
                
                if not brick_removed:
                    print(f"[MAP] WARNING: No se pudo conectar spawn {spawn_idx+1}")
                    break
                
                attempts += 1
            
            if attempts >= max_attempts:
                print(f"[MAP] ERROR: Max attempts para spawn {spawn_idx+1}")
    
    def _flood_fill(self, start_r, start_c):
        """Flood Fill retornando celdas alcanzables ('empty' y 'door')."""
        from collections import deque
        
        visited = set()
        queue = deque([(start_r, start_c)])
        visited.add((start_r, start_c))
        
        while queue:
            r, c = queue.popleft()
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                
                if (nr, nc) in visited:
                    continue
                
                if not (0 < nr < self.rows - 1 and 0 < nc < self.cols - 1):
                    continue
                
                if self.grid[nr][nc] in ['empty', 'door']:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        return visited
    
    def _remove_blocking_brick(self, reachable, door_r, door_c):
        """Busca y remueve el brick más cercano a la puerta que bloquea."""
        best_brick = None
        best_distance = 99999
        
        for r, c in reachable:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                
                if not (0 < nr < self.rows - 1 and 0 < nc < self.cols - 1):
                    continue
                
                if (nr, nc) in reachable:
                    continue
                
                if self.grid[nr][nc] == 'brick':
                    dist = abs(nr - door_r) + abs(nc - door_c)
                    
                    if dist < best_distance:
                        best_distance = dist
                        best_brick = (nr, nc)
        
        if best_brick:
            br, bc = best_brick
            self.grid[br][bc] = 'empty'
            print(f"[MAP] Brick removido en ({bc}, {br}) para conectar")
            return True
        
        return False

    def draw(self, screen, camera):
        """Dibuja el mapa con soporte para diagonal celda por celda."""
        if isinstance(camera, SplitCamera) and camera.split_mode == 'diagonal':
            self._draw_diagonal(screen, camera)
        elif isinstance(camera, SplitCamera):
            for surf, vp, _ in camera.iter_viewports(screen):
                self._draw_on(surf, vp)
        else:
            self._draw_on(screen, camera)

    def _draw_diagonal(self, screen, camera):
        """
        Dibuja el mapa en modo diagonal, celda por celda.
        
        Para cada celda, verifica si debe dibujarse en cada viewport
        usando camera.should_draw_at_position().
        """
        cs = self.cell_size
        
        # Dibujar para cada viewport
        for viewport_index, (surf, vp, flag) in enumerate(camera.iter_viewports(screen)):
            # Calcular rango visible
            sc = max(0, int(vp.x // cs))
            ec = min(self.cols, int((vp.x + camera.screen_w) // cs) + 2)
            sr = max(0, int(vp.y // cs))
            er = min(self.rows, int((vp.y + camera.screen_h) // cs) + 2)

            # Dibujar cada celda
            for r in range(sr, er):
                for c in range(sc, ec):
                    ct = self.grid[r][c]
                    if ct == 'empty':
                        continue
                    
                    tile = self.tiles.get(ct)
                    if not tile:
                        continue
                    
                    # Calcular posición en pantalla
                    world_x = c * cs
                    world_y = r * cs
                    screen_x, screen_y = vp.apply(world_x, world_y)
                    
                    # Verificar si esta celda debe dibujarse en este viewport
                    if camera.should_draw_at_position(screen_x, screen_y, viewport_index):
                        screen.blit(tile, (int(screen_x), int(screen_y)))

    def _draw_on(self, surf, cam):
        """Dibujado normal (no diagonal)."""
        cs   = self.cell_size
        zoom = getattr(cam, 'zoom', 1.0)
        ts   = max(1, int(cs * zoom))

        if hasattr(cam, 'screen_rect'):
            vw, vh = cam.screen_rect.width, cam.screen_rect.height
        else:
            vw, vh = cam.width, cam.height

        sc = max(0, int(cam.x // cs))
        ec = min(self.cols, int((cam.x + vw) // cs) + 2)
        sr = max(0, int(cam.y // cs))
        er = min(self.rows, int((cam.y + vh) // cs) + 2)

        for r in range(sr, er):
            for c in range(sc, ec):
                ct = self.grid[r][c]
                if ct == 'empty':
                    continue
                tile = self.tiles.get(ct)
                if tile:
                    sx, sy = cam.apply(c * cs, r * cs)
                    if zoom != 1.0:
                        surf.blit(pygame.transform.scale(tile, (ts, ts)),
                                  (int(sx), int(sy)))
                    else:
                        surf.blit(tile, (int(sx), int(sy)))

    def check_collision_with_blocks(self, rect):
        cs = self.cell_size
        lc = max(0, rect.left   // cs)
        rc = min(self.cols - 1, rect.right  // cs)
        tr = max(0, rect.top    // cs)
        br = min(self.rows - 1, rect.bottom // cs)

        for r in range(tr, br + 1):
            for c in range(lc, rc + 1):
                if self.grid[r][c] in ('ironbrick', 'brick'):
                    if rect.colliderect(pygame.Rect(c * cs, r * cs, cs, cs)):
                        return True
        return False

    def check_door_collision(self, rect):
        cs = self.cell_size
        door_rect = pygame.Rect(self.door_col * cs,
                                self.door_row * cs, cs, cs)
        return rect.colliderect(door_rect)


# Alias retrocompatibilidad
MultiCamera = SplitCamera