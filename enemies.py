"""
ENEMIES.PY - Enemigos con IA
=============================

Jerarquía de herencia:
    AnimatedEntity
     MovableEntity
         PathfindingEntity
             LivingEntity
                 Ghost, Snow, Bear, Robot, Water, Globe, Barrel

Todos los enemigos heredan de LivingEntity (excepto Barrel que hereda
directamente de LivingEntity sin PathfindingEntity). Esto les da:
- Animación (AnimatedEntity)
- Movimiento y colisiones (MovableEntity)
- Pathfinding A* y evasión de bombas (PathfindingEntity)
- Sistema de vidas y muerte (LivingEntity)

Clases:
-------

Ghost(LivingEntity):
    Fantasma que atraviesa paredes temporalmente.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - ghost_mode: Puede atravesar muros (2s duración, 10s cooldown)
    - Semi-transparente y con aura mientras está activo
    
    Atributos únicos:
    - ghost_mode: Estado de habilidad (bool)
    - ghost_mode_timer: Tiempo restante de habilidad
    - ghost_cooldown_timer: Cooldown hasta próxima activación
    
    Métodos principales:
    - activate_ghost_mode(): Activa modo fantasma
    - update_ghost_mode(): Maneja lógica de habilidad y teleporte
    - draw(): Renderizado con efecto de transparencia

Snow(LivingEntity):
    Enemigo que deja rastro de nieve que ralentiza.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - Cárea tiles de nieve al moverse
    - Las tiles ralentizan jugadores al pisarlas
    
    Atributos únicos:
    - snow_tiles: Lista de tiles de nieve activas
    - snow_trail_timer: Cooldown entre tiles
    
    Métodos principales:
    - cáreate_snow_trail(): Cárea tile de nieve en posición actual
    - update(): Cárea nieve periódicamente mientras se mueve

Bear(LivingEntity):
    Oso resistente que puede romper bricks.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - Puede romper bricks (bloques destructibles)
    - Olfatea para detectar jugadores lejos
    
    Atributos únicos:
    - sniff_timer: Cooldown de olfateo
    - sniff_target: Posición detectada por olfato
    - can_báreak_bricks: Puede romper bloques
    
    Métodos principales:
    - update_sniff(): Detecta jugador a distancia
    - try_báreak_brick(): Intenta romper brick en celda actual
    - draw(): Muestra indicador de olfateo

Robot(LivingEntity):
    Robot que coloca sus propias bombas.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - Coloca bombas propias (sprite diferente)
    - Las bombas de Robot no pueden empujar a jugadores
    
    Atributos únicos:
    - bombs: Lista de bombas del Robot
    - bomb_cooldown: Tiempo entre bombas
    - active_bomb_count: Cantidad de bombas activas
    - max_bombs: Máximo de bombas simultáneas
    
    Métodos principales:
    - place_bomb(): Coloca bomba en posición actual
    - update_bombs(): Actualiza bombas propias
    - draw(): Renderizado con indicador de bomba lista

Water(LivingEntity):
    Enemigo acuático que cárea charcos resbaladizos.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - Cárea charcos al moverse
    - Los charcos hacen resbalar a jugadores
    
    Atributos únicos:
    - water_puddles: Lista de charcos activos
    - puddle_timer: Cooldown entre charcos
    
    Métodos principales:
    - update(): Cárea charcos periódicamente
    - draw(): Renderiza charcos y enemigo

Globe(LivingEntity):
    Globo que vuela y suelta powerups para enemigos.
    
    Hereda de: LivingEntity
    
    Habilidad especial:
    - Vuela periódicamente (invulnerable mientras vuela)
    - Suelta powerups que benefician a enemigos
    
    Atributos únicos:
    - is_flying: Estado de vuelo
    - fly_timer: Timer hasta próximo vuelo
    - flight_offset: Offset visual de altura
    - enemy_powerups: Lista de powerups activos
    
    Métodos principales:
    - update(): Coordina vuelo y powerups
    - take_damage(): Solo recibe daño si no vuela
    - draw(): Renderiza con sombra cuando vuela

Barrel(LivingEntity):
    Barril que se mueve y spawna enemigos al morir.
    
    Hereda de: LivingEntity (con PathfindingEntity completo)
    
    Habilidad especial:
    - Al ser destruido spawna un enemigo aleatorio (Ghost, Snow, Bear o Water)
    - El enemigo spawneado aparece aturdido temporalmente
    
    Atributos únicos:
    - spawn_enemy_types: Lista de enemigos que puede spawnear
    - stun_duration: Duración del aturdimiento del enemigo spawneado
    
    Métodos principales:
    - die(): Spawna enemigo aleatorio en su posición
    - update(): Movimiento y comportamiento normal de enemigo

Sistema común a todos:
----------------------
- Detección de jugador en rango
- Pathfinding A* hacia jugador
- Evasión inteligente de bombas con tiempo de áreacción
- Estado WAIT después de huir (anti-vibración)
- Sistema de stun por bombas pateadas
- Animaciones por dirección

Configuración:
--------------
Cada enemigo tiene su config en settings.py:
- GhostConfig, SnowConfig, BearConfig, etc.
- Definen: velocidad, vidas, rango, cooldowns

Uso típico:
-----------
    # Cárear enemigo
    ghost = Ghost(pos=(x, y))
    
    # Actualizar cada frame
    ghost.update(dt, maze, player)
    
    # Dibujar
    ghost.draw(screen, camera)
"""


import pygame
import math
from entities import LivingEntity, load_animations_from_dict
from settings import GhostConfig, SnowConfig, BearConfig, BarrelConfig, RobotConfig, WaterConfig, GlobeConfig, CELL_SIZE
import random
from utils import load_image, pixel_to_grid, grid_to_pixel


# GHOST - Enemigo con modo fantasma

class Ghost(LivingEntity):
    """
    Fantasma que puede atravesar paredes temporalmente.
    
    Habilidad: Modo fantasma (2s duración, 10s cooldown)
    """
    
    def __init__(self, pos):
        # Configuración de animaciones
        animations_config = {
            'up': ['ghost_stand.png', 'ghost_move01.png', 'ghost_move02.png'],
            'down': ['ghost_sta.png', 'ghost_m01.png', 'ghost_m02.png'],
            'left': ['ghost_stand.png', 'ghost_move01.png', 'ghost_move02.png'],
            'right': ['ghost_sta.png', 'ghost_m01.png', 'ghost_m02.png'],
            'dead': ['enemy_fall.png', 'enemy_fall01.png', 'enemy_fall02.png', 'enemy_fall03.png']
        }
        
        animations = load_animations_from_dict(animations_config)
        
        # Inicializar clase base
        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=GhostConfig.SPEED,
            animations=animations,
            lives=GhostConfig.LIVES,
            detection_range=GhostConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=5
        )
        
        self._bomb_reaction_time = GhostConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Ghost'
        self.score_value = GhostConfig.SCORE
        
        # Habilidad de Ghost
        self.ghost_mode = False
        self.ghost_mode_duration = GhostConfig.GHOST_MODE_DURATION
        self.ghost_mode_timer = 0.0
        self.ghost_mode_cooldown = GhostConfig.GHOST_MODE_COOLDOWN
        self.ghost_cooldown_timer = 0.0
        
        self._returning_to_empty = False
        self._target_empty_pos = None
        self._return_speed_multiplier = 3
    
    def activate_ghost_mode(self):
        """Activa el modo fantasma si el cooldown está listo."""
        if self.ghost_cooldown_timer <= 0:
            self.ghost_mode = True
            self.ghost_mode_timer = self.ghost_mode_duration
            self.ghost_cooldown_timer = self.ghost_mode_cooldown
    
    def update_ghost_mode(self, dt, maze):
        """
        Actualiza el estado del modo fantasma.
        """
        if self.ghost_cooldown_timer > 0:
            self.ghost_cooldown_timer -= dt

        if self.ghost_mode:
            if self._returning_to_empty and self._target_empty_pos:
                target_x, target_y = self._target_empty_pos
                dx = target_x - self.x
                dy = target_y - self.y
                distance = (dx**2 + dy**2)**0.5
                
                if distance < 10:
                    # Llegó - snap final y desactivar
                    self.x = target_x
                    self.y = target_y
                    self.rect.topleft = (self.x, self.y)
                    self.pos = (self.x, self.y)  #  También actualizar pos
                    self.ghost_mode = False
                    self.ghost_mode_timer = 0.0
                    self._returning_to_empty = False
                    self._target_empty_pos = None
                    self.direction = (0, 0)
                else:
                    speed = self.speed * self._return_speed_multiplier
                    if distance > 0:
                        # Calcular movimiento
                        move_x = (dx / distance) * speed * dt
                        move_y = (dy / distance) * speed * dt
                        
                        self.x += move_x
                        self.y += move_y
                        self.rect.topleft = (self.x, self.y)
                        self.pos = (self.x, self.y)
                        
                        # Actualizar dirección SOLO para animación
                        if abs(dx) > abs(dy):
                            self.direction = (1 if dx > 0 else -1, 0)
                        else:
                            self.direction = (0, 1 if dy > 0 else -1)
                
                return  #  NO hacer nada más durante retorno
            
                        # RESTRICCION: No salir del area jugable
            row = int(self.y // maze.cell_size)
            col = int(self.x // maze.cell_size)
            
            if row <= 0 or row >= maze.rows - 1 or col <= 0 or col >= maze.cols - 1:
                # Forzar regreso
                row = max(1, min(row, maze.rows - 2))
                col = max(1, min(col, maze.cols - 2))
                self.y = row * maze.cell_size + maze.cell_size // 2
                self.x = col * maze.cell_size + maze.cell_size // 2
            
            # Timer normal
            self.ghost_mode_timer -= dt

            cs  = maze.cell_size
            col = int(self.x // cs)
            row = int(self.y // cs)

            # Bug #3: expulsar del borde del mapa
            out_of_bounds = (
                row <= 0 or row >= maze.rows - 1 or
                col <= 0 or col >= maze.cols - 1
            )
            if out_of_bounds:
                safe_col = max(1, min(col, maze.cols - 2))
                safe_row = max(1, min(row, maze.rows - 2))
                self.x = safe_col * cs
                self.y = safe_row * cs
                self.rect.topleft = (self.x, self.y)
                self.pos = (self.x, self.y)
                self.ghost_mode = False
                self.ghost_mode_timer = 0.0
                return

            if 0 <= row < maze.rows and 0 <= col < maze.cols:
                cell_type = maze.grid[row][col]

                if self.ghost_mode_timer <= 0:
                    if cell_type == 'empty':
                        self.ghost_mode = False
                    else:
                        nearest = self._find_nearest_empty(maze, row, col)
                        if nearest:
                            nr, nc = nearest
                            self._target_empty_pos = (nc * cs, nr * cs)
                            self._returning_to_empty = True
                            self.ghost_mode_timer = 20.0
                        else:
                            self.ghost_mode_timer = 0.1
    
    def _find_nearest_empty(self, maze, start_row, start_col):
        """
        BFS desde (start_row, start_col) buscando la celda 'empty' mas cercana
        dentro del area jugable.

        Returns:
            (row, col) de la celda empty mas cercana, o None si no hay ninguna.
        """
        from collections import deque
        visited = set()
        queue   = deque()
        queue.append((start_row, start_col))
        visited.add((start_row, start_col))

        while queue:
            r, c = queue.popleft()
            if (0 < r < maze.rows - 1 and 0 < c < maze.cols - 1 and
                    maze.grid[r][c] == 'empty'):
                return (r, c)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) not in visited and 0 <= nr < maze.rows and 0 <= nc < maze.cols:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return None

    def move(self, dt, maze):
        """Override para incluir logica de ghost mode."""
        collided = super().move(dt, maze, ignore_collisions=self.ghost_mode)

        # Activar ghost mode si choca (solo en modo normal)
        if collided and not self.ghost_mode:
            self.activate_ghost_mode()
    
    def update(self, dt, maze, player):
        """Actualizacion principal del Ghost."""
        if not self.dead:

            # WAIT state check (previene vibración)
            if self.update_wait_state(dt):
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return
                        #  FIX v3: PRIORIDAD ABSOLUTA al retorno
            if self._returning_to_empty:
                self.direction = (0, 0)  # Forzar
                self.update_ghost_mode(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=True)
                return
            
            # Resto del código original...
            player_bombs = getattr(player, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                if not self.ghost_mode:
                    self.ghost_mode = True
                    self.ghost_mode_timer = 0.0
                self._move_toward_cell(escape_cell, maze, dt)
                self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

            self.update_ghost_mode(dt, maze)
            distance = math.hypot(player.x - self.x, player.y - self.y)
            detection_distance = self.detection_range * maze.cell_size

            if distance <= detection_distance:
                self.follow_player(maze, player, dt)
            else:
                self.random_walk(dt)

            self.move(dt, maze)

        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))
    
    def draw(self, screen, camera):
        """Dibujado personalizado con efecto de ghost mode."""
        if not self.image:
            return

        screen_x, screen_y = camera.apply(self.x, self.y)
        zoom = getattr(camera, 'zoom', 1.0)
        img  = self.image
        if zoom != 1.0:
            sw = max(1, int(img.get_width()  * zoom))
            sh = max(1, int(img.get_height() * zoom))
            img = pygame.transform.scale(img, (sw, sh))

        if self.ghost_mode:
            ghost_img = img.copy()
            ghost_img.set_alpha(150)
            screen.blit(ghost_img, (int(screen_x), int(screen_y)))
            pulse = abs(math.sin(self.ghost_mode_timer * 5)) * 20
            pygame.draw.circle(screen, (200, 200, 255),
                             (int(screen_x) + img.get_width()//2,
                              int(screen_y) + img.get_height()//2),
                             int(20 + pulse), 2)
        else:
            super().draw(screen, camera)
            img = self.image  # super() ya dibujo; reutilizamos img para overlays

        #  Efectos visuales siempre visibles (stun + '!') 
        if self._kick_stun_timer > 0:
            self._draw_stun_stars(screen, screen_x, screen_y, img, zoom)
        if self._exclamation_timer > 0:
            self._draw_exclamation(screen, screen_x, screen_y, img, zoom)


# SNOW - Enemigo que deja rastro de nieve

class Snow(LivingEntity):
    """
    Enemigo que deja rastro de nieve que ralentiza.
    
    Habilidad: Deja bloques de nieve cada 0.5s
    """
    
    def __init__(self, pos):
        # Configuración de animaciones
        animations_config = {
            'up': ['snow.png'],
            'down': ['snow.png'],
            'left': ['snow_stand.png', 'snow_move01.png', 'snow_move02.png'],
            'right': ['snow_sta.png', 'snow_m01.png', 'snow_m02.png'],
            'dead': ['enemy_fall.png', 'enemy_fall01.png', 'enemy_fall02.png', 'enemy_fall03.png']
        }
        
        animations = load_animations_from_dict(animations_config)
        
        # Inicializar clase base
        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=SnowConfig.SPEED,
            animations=animations,
            lives=SnowConfig.LIVES,
            detection_range=SnowConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=5
        )
        
        self._bomb_reaction_time = SnowConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Snow'
        self.score_value = SnowConfig.SCORE
        
        # Habilidad de Snow
        self.snow_trail_interval = SnowConfig.SNOW_TRAIL_INTERVAL
        self.snow_trail_timer = 0.0
        self.last_snow_pos = None
    
    def create_snow_trail(self, snow_tiles_list):
        """
        Crea un bloque de nieve en la posición actual.
        
        Args:
            snow_tiles_list: Lista donde agregar el SnowTile
        """
        from powerups import SnowTile
        
        # Alinear al grid
        grid_x = (int(self.x) // CELL_SIZE) * CELL_SIZE
        grid_y = (int(self.y) // CELL_SIZE) * CELL_SIZE
        current_pos = (grid_x, grid_y)
        
        # Solo crear si es una nueva posición
        if self.last_snow_pos != current_pos:
            snow_tile = SnowTile(current_pos)
            snow_tiles_list.append(snow_tile)
            self.last_snow_pos = current_pos
    
    def update(self, dt, maze, player, snow_tiles_list):
        """Actualizacion principal del Snow."""
        if not self.dead:
            # WAIT state check (previene vibración)
            if self.update_wait_state(dt):
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return
            
            #  Evasion de bombas del jugador con reaction_time 
            player_bombs = getattr(player, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

            distance = math.hypot(player.x - self.x, player.y - self.y)
            detection_distance = self.detection_range * maze.cell_size

            if distance <= detection_distance:
                self.follow_player(maze, player, dt)
            else:
                self.random_walk(dt)

            self.move(dt, maze)

            # Crear rastro de nieve
            self.snow_trail_timer += dt
            if self.snow_trail_timer >= self.snow_trail_interval:
                self.create_snow_trail(snow_tiles_list)
                self.snow_trail_timer = 0.0

        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))


# BEAR - Enemigo que rompe ladrillos

class Bear(LivingEntity):
    """
    Oso que puede romper ladrillos y olfatear al jugador.
    
    Habilidades:
    - Rompe ladrillos (2 golpes)
    - Olfateo cada 5s (detecta sin límite de rango por 2s)
    """
    
    def __init__(self, pos):
        # Configuración de animaciones
        animations_config = {
            'up': ['bear.png'],
            'down': ['bear.png'],
            'left': ['bear_stand.png', 'bear_move01.png', 'bear_move02.png'],
            'right': ['bear_sta.png', 'bear_mov01.png', 'bear_mov02.png'],
            'dead': ['enemy_fall.png', 'enemy_fall01.png', 'enemy_fall02.png', 'enemy_fall03.png']
        }
        
        animations = load_animations_from_dict(animations_config)
        
        # Inicializar clase base
        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=BearConfig.SPEED,
            animations=animations,
            lives=BearConfig.LIVES,
            detection_range=BearConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=5
        )
        
        self._bomb_reaction_time = BearConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Bear'
        self.score_value = BearConfig.SCORE
        
        # Habilidad de romper ladrillos
        self.can_break_bricks = True
        self.brick_damage = {}  # {(row, col): damage_count}
        self.break_cooldown = BearConfig.BREAK_COOLDOWN
        self.break_timer = 0.0
        
        # Habilidad de olfateo
        self.sniff_interval   = BearConfig.SNIFF_INTERVAL
        self.sniff_timer      = 0.0
        self.sniff_duration   = BearConfig.SNIFF_DURATION
        self.sniff_active     = False
        self.sniff_active_timer = 0.0
        # Target fijado al activar el olfateo (evita cambiar de objetivo mid-sniff)
        self.sniff_target = None
    
    def update_sniff(self, dt, player=None):
        """Actualiza el sistema de olfateo. Captura el target al activar."""
        self.sniff_timer += dt

        if self.sniff_timer >= self.sniff_interval:
            self.sniff_timer = 0.0
            self.sniff_active = True
            self.sniff_active_timer = self.sniff_duration
            # Fijar target al jugador actual en el momento de activar el olfateo
            self.sniff_target = player

        if self.sniff_active:
            self.sniff_active_timer -= dt
            if self.sniff_active_timer <= 0:
                self.sniff_active = False
                self.sniff_target = None
    
    def try_break_brick(self, maze, player):
        """
        Intenta romper un ladrillo frente a Bear.
        
        Args:
            maze: Instancia del laberinto
            player: Instancia del jugador
        
        Returns:
            bool: True si golpeó un ladrillo
        """
        # Solo romper si está persiguiendo o olfateando
        distance = math.hypot(player.x - self.x, player.y - self.y)
        if not self.sniff_active and distance > self.detection_range * maze.cell_size:
            return False
        
        if self.break_timer > 0:
            return False
        
        # Calcular celda frente a Bear
        look_ahead = 1
        if self.direction == (1, 0):
            target_col = int(self.x // maze.cell_size) + look_ahead
            target_row = int(self.y // maze.cell_size)
        elif self.direction == (-1, 0):
            target_col = int(self.x // maze.cell_size) - look_ahead
            target_row = int(self.y // maze.cell_size)
        elif self.direction == (0, 1):
            target_col = int(self.x // maze.cell_size)
            target_row = int(self.y // maze.cell_size) + look_ahead
        elif self.direction == (0, -1):
            target_col = int(self.x // maze.cell_size)
            target_row = int(self.y // maze.cell_size) - look_ahead
        else:
            return False
        
        # Verificar límites
        if not (0 <= target_row < maze.rows and 0 <= target_col < maze.cols):
            return False
        
        # Verificar que sea ladrillo
        if maze.grid[target_row][target_col] != 'brick':
            return False
        
        # Golpear ladrillo
        brick_key = (target_row, target_col)
        
        if brick_key not in self.brick_damage:
            self.brick_damage[brick_key] = 0
        
        self.brick_damage[brick_key] += 1
        
        # Romper si recibió suficientes golpes
        if self.brick_damage[brick_key] >= BearConfig.BRICK_HITS_TO_BREAK:
            maze.grid[target_row][target_col] = 'empty'
            del self.brick_damage[brick_key]
        
        self.break_timer = self.break_cooldown
        return True
    
    def update(self, dt, maze, player, robot_bombs=None):
        """Actualizacion principal del Bear."""
        if not self.dead:
            # WAIT state check (previene vibración)
            if self.update_wait_state(dt):
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return
            
            if self.break_timer > 0:
                self.break_timer -= dt

            #  Evasion de bombas del jugador con reaction_time 
            player_bombs = getattr(player, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

            self.update_sniff(dt, player)
            target = self.sniff_target if (self.sniff_active and self.sniff_target) else player
            if target is None or getattr(target, 'dead', False) or getattr(target, 'finish', False):
                target = player

            distance = math.hypot(target.x - self.x, target.y - self.y)
            detection_distance = self.detection_range * maze.cell_size

            if distance <= detection_distance or self.sniff_active:
                self.follow_player(maze, target, dt,
                                   ignore_bricks=self.sniff_active,
                                   robot_bombs=robot_bombs)
                self.try_break_brick(maze, target)
            else:
                self.random_walk(dt)

            self.move(dt, maze)

        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))
    
    def draw(self, screen, camera):
        """Dibujado personalizado con indicador de olfateo."""
        # Dibujo normal
        super().draw(screen, camera)
        
        # Indicador de olfateo
        if self.sniff_active and not self.dead:
            screen_x, screen_y = camera.apply(self.x, self.y)
            pulse = abs(math.sin(self.sniff_active_timer * 8)) * 10
            pygame.draw.circle(screen, (255, 100, 100),
                             (screen_x + 16, screen_y + 16),
                             int(25 + pulse), 3)


# BARREL - Barril que esconde un enemigo

class Barrel(LivingEntity):
    """
    Barril que rueda lentamente hacia Bomberman.
    Al morir, libera un enemigo aleatorio que sale aturdido.

    Habilidad: Al destruirse, spawna 1 enemigo (según probabilidades)
               que aparece paralizado STUN_DURATION segundos.

    El tipo de enemigo a spawnear se elige en die() y se guarda en
    self.pending_spawn para que game_level lo lea y cree el enemigo.
    """

    def __init__(self, pos):
        animations_config = {
            'up':    ['barrel.png'],
            'down':  ['barrel.png'],
            'left':  ['barrel_stand.png', 'barrel_move01.png', 'barrel_move02.png'],
            'right': ['barrel_sta.png',   'barrel_m01.png',  'barrel_m02.png'],
            'dead':  ['enemy_fall.png', 'enemy_fall01.png',
                      'enemy_fall02.png', 'enemy_fall03.png']
        }

        animations = load_animations_from_dict(animations_config)

        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=BarrelConfig.SPEED,
            animations=animations,
            lives=BarrelConfig.LIVES,
            detection_range=BarrelConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=5
        )

        self._bomb_reaction_time = BarrelConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Barrel'
        self.score_value = BarrelConfig.SCORE

        # game_level lee este campo al detectar barrel.remove == True.
        # Contiene el tipo de enemigo a crear ('ghost', 'snow', 'bear')
        # o None si no hay nada que spawnear todavía.
        self.pending_spawn = None

    # ---- Utilidades ----

    @staticmethod
    def _pick_spawn_type():
        """Elige el tipo de enemigo según probabilidades de BarrelConfig."""
        weighted = []
        for etype, prob in BarrelConfig.SPAWN_PROBABILITIES.itemás():
            weighted.extend([etype] * int(prob * 100))
        return random.choice(weighted)

    # ---- Override de die() ----

    def die(self):
        """
        Al morir, elige qué enemigo saldrá y lo guarda en pending_spawn.
        game_level crea el enemigo real cuando detecta self.remove == True.
        """
        super().die()  # Marca dead=True, cambia animación a 'dead'

        # Elegir cuántos y qué tipo spawnear
        spawns = []
        for _ in range(BarrelConfig.SPAWN_COUNT):
            spawns.append(self._pick_spawn_type())
        self.pending_spawn = spawns  # Lista de tipos, ej: ['ghost']

    # ---- Update ----

    def update(self, dt, maze, player):
        """Actualizacion principal del Barrel."""
        if not self.dead:
            #  Evasion de bombas del jugador con reaction_time 
            player_bombs = getattr(player, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

            distance = math.hypot(player.x - self.x, player.y - self.y)
            detection_distance = self.detection_range * maze.cell_size

            if distance <= detection_distance:
                self.follow_player(maze, player, dt)
            else:
                self.random_walk(dt)

            self.move(dt, maze)

        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))

# ROBOT - Bomberman enemigo con IA táctica

class Robot(LivingEntity):
    """
    Robot: enemigo que se comporta como un Bomberman malo.

    Mecánicas:
    - Siempre conoce la posición del jugador (DETECTION_RANGE ilimitado).
    - Ciclo GPS: avanza GPS_ACTIVE_TIME segundos, se detiene GPS_INACTIVE_TIME.
      Si el jugador está a ≤ GPS_KEEP_ON_RANGE celdas, el GPS no se apaga.
    - Coloca bombas con sprite_prefix='robot_' al estar a rango del jugador.
    - Escapa de cualquier bomba peligrosa (propia o de jugadores).
    - Evalúa patear su bomba hacia el jugador cuando están alineados.
    - Sus bombas NO dañan aliados (bomb._robot_owner=True).
    - Los jugadores pueden patear su bomba igual que la suya.
    - Sprites: robot_front_stand.png, robot_back_stand.png, etc.
    """

    # Estados internos del ciclo GPS
    STATE_CHASING  = 'chasing'    # avanza hacia el jugador con A*
    STATE_ESCAPING = 'escaping'   # huye de una bomba peligrosa
    STATE_INACTIVE = 'inactive'   # GPS apagado, quieto

    def __init__(self, pos):
        p = 'robot_'
        animations_config = {
            'down':  [f'{p}front_stand.png', f'{p}front_m01.png', f'{p}front_m02.png'],
            'up':    [f'{p}back_stand.png',  f'{p}back_m01.png',  f'{p}back_m02.png'],
            'left':  [f'{p}left_stand.png',  f'{p}left_m01.png',  f'{p}left_m02.png'],
            'right': [f'{p}right_stand.png', f'{p}right_m01.png', f'{p}right_m02.png'],
            'dead':  [f'{p}dead.png', f'{p}dead01.png', f'{p}dead02.png',
                      f'{p}dead03.png', f'{p}dead04.png', f'{p}dead05.png',
                      f'{p}dead06.png'],
        }
        animations = load_animations_from_dict(animations_config)

        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=RobotConfig.SPEED,
            animations=animations,
            lives=RobotConfig.LIVES,
            detection_range=RobotConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=8
        )

        self.enemy_type  = 'Robot'
        self.score_value = RobotConfig.SCORE

        #  Bombas 
        self.bombs            = []
        self.bomb_range       = RobotConfig.BOMB_RANGE
        self._bomb_cooldown   = 0.0     # tiempo hasta que puede volver a poner bomba
        self._active_count    = 0       # bombas activas actualmente

        #  Ciclo GPS 
        self._state     = self.STATE_CHASING
        self._gps_timer = RobotConfig.GPS_ACTIVE_TIME   # cuenta regresiva del estado actual
        self._escape_target = None                       # celda (row, col) de escape

    # GESTIÓN DE BOMBAS

    def _active_bombs(self):
        """Devuelve solo las bombas no removidas."""
        return [b for b in self.bombs if not getattr(b, 'remove', False)]

    def _place_bomb(self, maze):
        """
        Coloca una bomba en la celda actual si el cooldown está listo
        y no ha alcanzado el máximo simultáneo.
        Retorna la Bomb creada o None.
        """
        # BUG FIX: nunca colocar bomba si está aturdido (evita auto-stun)
        if self.is_stunned:
            return None
        if self._bomb_cooldown > 0:
            return None
        if len(self._active_bombs()) >= RobotConfig.MAX_BOMBS:
            return None

        from bomb import Bomb
        cs = maze.cell_size
        grid_x = (int(self.x + self.width  // 2) // cs) * cs
        grid_y = (int(self.y + self.height // 2) // cs) * cs

        # No poner dos bombas en la misma celda
        new_cell = (grid_y // cs, grid_x // cs)
        for b in self.bombs:
            if (int(b.y // cs), int(b.x // cs)) == new_cell:
                return None

        bomb = Bomb((grid_x, grid_y), sprite_prefix='robot_')
        bomb.explosion_range = self.bomb_range
        self.bombs.append(bomb)
        self._active_count += 1
        self._bomb_cooldown = RobotConfig.BOMB_COOLDOWN
        return bomb

    def update_bombs(self, dt, maze):
        """
        Actualiza bombas propias y las elimina cuando terminan.
        
        NUEVO: Usa _other_bombs si está disponible (para colisión bomba-bomba)
        """
        other_bombs_list = getattr(self, '_other_bombs', None)
        
        for bomb in self.bombs[:]:
            # Filtrar la bomba actual de la lista
            if other_bombs_list:
                other_bombs = [b for b in other_bombs_list if b is not bomb]
            else:
                other_bombs = None
            
            bomb.update(dt, maze, self, other_bombs)   # self como 'bomberman' para el kick
            if bomb.remove:
                self.bombs.remove(bomb)
                self._active_count = max(0, self._active_count - 1)

    # KICK INTELIGENTE

    def _try_smart_kick(self, player, maze):
        """
        Evalúa si conviene patear la bomba activa hacia el jugador.

        Condiciones para patear:
        1. Hay exactamente 1 bomba propia activa (no explotada, no siendo pateada).
        2. La bomba está en la misma fila O misma columna que el jugador.
        3. El jugador está a ≤ KICK_ALIGN_RANGE celdas de la bomba en ese eje.
        4. No hay ironbrick entre bomba y jugador.
        5. Robot está en la celda opuesta adyacente a la bomba (es quien la patea).
        """
        active = self._active_bombs()
        if len(active) != 1:
            return
        bomb = active[0]
        
        # CORREGIDO: No patear bombas de GPS
        if getattr(bomb, '_gps_break_bomb', False):
            return
        
        if bomb.exploded or bomb.is_being_kicked:
            return

        cs = maze.cell_size
        bomb_col = int(bomb.x // cs)
        bomb_row = int(bomb.y // cs)

        if hasattr(player, 'hitbox_offset_x'):
            px = player.x + player.hitbox_offset_x + player.width  // 2
            py = player.y + player.hitbox_offset_y + player.height // 2
        else:
            px = player.x + player.width  // 2
            py = player.y + player.height // 2
        p_col = int(px // cs)
        p_row = int(py // cs)

        # Determinar eje de alineación
        if bomb_row == p_row:
            kick_dir = (1 if p_col > bomb_col else -1, 0)
            dist     = abs(p_col - bomb_col)
            dr, dc   = 0, kick_dir[0]
        elif bomb_col == p_col:
            kick_dir = (0, 1 if p_row > bomb_row else -1)
            dist     = abs(p_row - bomb_row)
            dr, dc   = kick_dir[1], 0
        else:
            return  # no alineados

        if dist > RobotConfig.KICK_ALIGN_RANGE:
            return

        # Verificar que no haya ironbrick entre bomba y jugador
        for step in range(1, dist):
            r = bomb_row + dr * step
            c = bomb_col + dc * step
            if 0 <= r < maze.rows and 0 <= c < maze.cols:
                if maze.grid[r][c] == 'ironbrick':
                    return

        # Robot debe estar en la celda opuesta a la dirección del kick
        my_col = int(self.x // cs)
        my_row = int(self.y // cs)
        if (my_row, my_col) != (bomb_row - dr, bomb_col - dc):
            return

        # Patear
        bomb.kick_direction  = kick_dir
        bomb.is_being_kicked = True
        bomb.kick_distance   = 0

    # CICLO GPS

    def _update_gps(self, dt, player, maze):
        """
        Gestiona el ciclo GPS.
        Retorna True si Robot debe moverse este frame, False si debe quedarse quieto.

        FIX: Si el jugador esta a distancia <= GPS_KEEP_ON_RANGE el Robot SIEMPRE
        persigue (instinto basico), aunque el GPS este INACTIVE.
        Esto evita que parezca ciego cuando Bomberman esta justo al lado.
        """
        cs = maze.cell_size
        dist_cells = (abs(player.x - self.x) + abs(player.y - self.y)) / cs

        # Evasion tiene prioridad total
        if self._state == self.STATE_ESCAPING:
            return True

        # FIX: si el jugador esta MUY cerca, reactivar GPS inmediatamente
        if dist_cells <= RobotConfig.GPS_KEEP_ON_RANGE:
            if self._state == self.STATE_INACTIVE:
                self._state     = self.STATE_CHASING
                self._gps_timer = RobotConfig.GPS_ACTIVE_TIME
            return True

        self._gps_timer -= dt

        if self._state == self.STATE_CHASING:
            if self._gps_timer <= 0:
                # Apagar GPS (jugador lejos)
                self._state     = self.STATE_INACTIVE
                self._gps_timer = RobotConfig.GPS_INACTIVE_TIME
                self.direction  = (0, 0)
            return True

        elif self._state == self.STATE_INACTIVE:
            if self._gps_timer <= 0:
                self._state     = self.STATE_CHASING
                self._gps_timer = RobotConfig.GPS_ACTIVE_TIME
                return True
            return False   # quieto mientras GPS apagado Y jugador lejos

        return True

    # GPS — DETECTAR BRICK BLOQUEANTE Y ROMPERLO CON BOMBA
    # Igual que Bear.try_break_brick pero con bomba en vez de golpe físico

    STATE_GPS_BREAKING = 'gps_breaking'   # esperando que explote la bomba de GPS

    def _brick_blocking_path(self, maze, player):
        """
        Devuelve (brick_row, brick_col) del primer brick que bloquea el camino
        hacia el jugador, o None si ya hay camino libre.
        """
        cs = maze.cell_size
        my_row = int((self.y + self.height // 2) // cs)
        my_col = int((self.x + self.width  // 2) // cs)

        if hasattr(player, 'hitbox_offset_x'):
            px = player.x + player.hitbox_offset_x + player.width  // 2
            py = player.y + player.hitbox_offset_y + player.height // 2
        else:
            px = player.x + player.width  // 2
            py = player.y + player.height // 2
        p_row, p_col = int(py // cs), int(px // cs)

        # Camino normal libre  no hace falta romper nada
        if self.find_path(maze, (my_row, my_col), (p_row, p_col),
                          ignore_bricks=False):
            return None

        # Camino ideal (atraviesa bricks)
        ideal = self.find_path(maze, (my_row, my_col), (p_row, p_col),
                               ignore_bricks=True)
        if not ideal:
            return None

        # Primer brick del camino ideal
        for step_row, step_col in ideal:
            if maze.grid[step_row][step_col] == 'brick':
                return (step_row, step_col)
        return None

    def _place_bomb_to_break(self, maze, brick_row, brick_col):
        """
        Coloca bomba apuntando al brick si está dentro del rango.
        NO verifica zona segura porque el objetivo ES destruir ese brick.
        Retorna True si colocó la bomba.
        """
        if self._bomb_cooldown > 0 or self._active_bombs():
            return False

        cs = maze.cell_size
        my_row = int((self.y + self.height // 2) // cs)
        my_col = int((self.x + self.width  // 2) // cs)
        dist   = abs(brick_row - my_row) + abs(brick_col - my_col)

        # CORREGIDO: Solo colocar si está adyacente al brick (dist == 1)
        # Esto GARANTIZA que la bomba siempre alcanzará el brick
        if dist != 1:
            return False   # No adyacente, seguir acercándose
        
        # Verificación adicional: brick debe estar en rango de explosión
        if dist > RobotConfig.BOMB_RANGE:
            return False

        grid_x = my_col * cs
        grid_y = my_row * cs
        for b in self.bombs:
            if (int(b.y // cs), int(b.x // cs)) == (my_row, my_col):
                return False

        from bomb import Bomb
        bomb = Bomb((grid_x, grid_y), sprite_prefix='robot_')
        bomb.explosion_range = RobotConfig.BOMB_RANGE
        # Marcar que esta bomba NO debe ser pateada (es para romper brick)
        bomb._gps_break_bomb = True
        bomb.can_be_kicked = False  # CORREGIDO: Prevenir pateo accidental
        self.bombs.append(bomb)
        self._active_count  += 1
        self._bomb_cooldown  = RobotConfig.BOMB_COOLDOWN
        return True

    # UPDATE PRINCIPAL

    def stun(self, duration):
        """Override: al ser aturdido, resetear GPS a CHASING para evitar quedar inmovil."""
        super().stun(duration)
        # Forzar GPS activo cuando se recupere del stun
        self._state     = self.STATE_CHASING
        self._gps_timer = RobotConfig.GPS_ACTIVE_TIME

    def update(self, dt, maze, player):
        if self.dead:
            self.update_death(dt)
            self.animate(dt, moving=False)
            return

        #  BUG FIX: stun bloquea TODO: GPS, bombs, movimiento 
        if self.is_stunned:
            self.update_bombs(dt, maze)
            self.update_death(dt)
            self.animate(dt, moving=False)
            return

        # Timer de cooldown de bomba
        if self._bomb_cooldown > 0:
            self._bomb_cooldown -= dt

        #  Detectar peligro de bomba (propia + jugador) 
        dangerous = list(self.bombs)
        if hasattr(player, 'bombs'):
            dangerous += [b for b in player.bombs
                          if not getattr(b, 'remove', False)]

        bomb_threat, escape_cell = self._nearby_bomb_danger(
            dangerous, RobotConfig.ESCAPE_RADIUS
        )

        # Si está escapando, SOLO escapar
        if bomb_threat is not None and escape_cell is not None:
            self._state         = self.STATE_ESCAPING
            self._escape_target = escape_cell
            self._move_toward_cell(self._escape_target, maze, dt)
            self.update_bombs(dt, maze)
            self.move(dt, maze)
            self.update_death(dt)
            self.animate(dt, moving=(self.direction != (0, 0)))
            return
        
        elif self._state == self.STATE_ESCAPING:
            self._state         = self.STATE_CHASING
            self._gps_timer     = RobotConfig.GPS_ACTIVE_TIME
            self._escape_target = None

        #  Movimiento según estado (solo si NO está escapando) 
        if self._update_gps(dt, player, maze):
            cs = maze.cell_size
            if hasattr(player, 'hitbox_offset_x'):
                px = player.x + player.hitbox_offset_x + player.width  // 2
                py = player.y + player.hitbox_offset_y + player.height // 2
            else:
                px = player.x + player.width  // 2
                py = player.y + player.height // 2
            dist_to_player = (
                abs(int(px // cs) - int((self.x + self.width  // 2) // cs)) +
                abs(int(py // cs) - int((self.y + self.height // 2) // cs))
            )

            #  GPS: detectar brick bloqueante 
            # Solo buscar brick si no hay bomba activa de GPS pendiente
            gps_bombs = [b for b in self._active_bombs()
                         if getattr(b, '_gps_break_bomb', False)]
            brick_target = None
            if not gps_bombs:
                brick_target = self._brick_blocking_path(maze, player)

            if brick_target:
                # Hay brick bloqueando  moverse hacia él (camino ideal)
                self.follow_player(maze, player, dt, ignore_bricks=True)
                # Intentar poner bomba cuando esté cerca del brick
                placed = self._place_bomb_to_break(maze, *brick_target)
                # No patear ninguna bomba en este modo (evita accidente)
                # No llamar _try_smart_kick

            else:
                # Camino libre  perseguir normalmente
                self.follow_player(maze, player, dt, ignore_bricks=False)

                # Poner bomba si el jugador está cerca
                if dist_to_player <= RobotConfig.BOMB_PLACE_RANGE:
                    self._place_bomb(maze)

                # CORREGIDO: Kick inteligente solo si NO hay bombas GPS
                if self._active_bombs() and not gps_bombs:
                    self._try_smart_kick(player, maze)

        #  Actualizar bombas propias 
        self.update_bombs(dt, maze)

        self.move(dt, maze)
        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))

    def draw(self, screen, camera):
        """Dibuja Robot con bombillo rojo parpadeante cuando el GPS está activo."""
        super().draw(screen, camera)

        if self.dead or not self.image:
            return

        #  Bombillo GPS (igual que el humo de olfateo de Bear) 
        # Activo cuando STATE_CHASING o GPS_BREAKING (NO cuando escaping/inactive)
        gps_on = (self._state == self.STATE_CHASING)
        if gps_on:
            import math, time
            screen_x, screen_y = camera.apply(self.x, self.y)
            zoom = getattr(camera, 'zoom', 1.0)
            w = max(1, int(self.image.get_width()  * zoom))

            # Pulso: alterna rojo brillante ↔ rojo oscuro
            pulse = math.sin(time.time() * 8)   # 8 rad/s  ~1.3 Hz
            r = int(220 + 35 * pulse)
            g = int(20  + 10 * pulse)

            # Centro sobre la cabeza del sprite
            cx = int(screen_x + w // 2)
            cy = int(screen_y - int(5 * zoom))
            radius = max(3, int(5 * zoom))

            # Resplandor exterior semitransparente
            glow = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (r, g, 0, 60), (radius*2, radius*2), radius*2)
            screen.blit(glow, (cx - radius*2, cy - radius*2))

            # Bombillo rojo sólido
            pygame.draw.circle(screen, (r, g, 0), (cx, cy), radius)
            pygame.draw.circle(screen, (255, 200, 0), (cx, cy), radius, 1)

# WATER - Enemigo teletransportador

class Water(LivingEntity):
    """
    Enemigo Water que se teletransporta cerca del jugador y deja charcos resbaladizos.
    
    Habilidades:
    - Teletransporte cercano al jugador cada 4 segundos
    - Deja charcos que hacen resbalar al jugador
    - Animación de desaparición/aparición
    """
    
    def __init__(self, pos):
        # Configuración de animaciones
        animations_config = {
            'up':    ['water.png'],
            'down':  ['water.png'],
            'left':  ['water_stand.png', 'water_move01.png', 'water_move02.png'],
            'right': ['water_sta.png',   'water_m01.png',  'water_m02.png'],
            'dead':  ['enemy_fall.png', 'enemy_fall01.png', 'enemy_fall02.png', 'enemy_fall03.png'],
            'teleport_out': ['water_teleport01.png', 'water_teleport02.png', 'water_teleport03.png'],
            'teleport_in': ['water_teleport03.png', 'water_teleport02.png', 'water_teleport01.png']
        }
        
        animations = load_animations_from_dict(animations_config)
        
        # Inicializar clase base
        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=WaterConfig.SPEED,
            animations=animations,
            lives=WaterConfig.LIVES,
            detection_range=WaterConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=8
        )
        
        self._bomb_reaction_time = WaterConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Water'
        self.score_value = WaterConfig.SCORE
        
        # Sistema de teletransporte
        self.teleport_cooldown = WaterConfig.TELEPORT_COOLDOWN
        self.teleport_timer = self.teleport_cooldown
        self.is_teleporting = False
        self.teleport_phase = None  # 'out' o 'in'
        self.teleport_animation_timer = 0.0
        self.teleport_target = None
        
        # Charcos
        self.puddle_timer = WaterConfig.PUDDLE_DROP_INTERVAL
        self.puddles = []  # Lista de charcos activos
    
    def update(self, dt, maze, target=None):
        """Actualización con teletransporte y charcos."""
        if self.dead:
            self.update_death(dt)
            self.animate(dt, moving=False)
            return

        # WAIT state check (previene vibración)
        if self.update_wait_state(dt):
            self._update_teleport(dt, maze, target)
            for puddle in self.puddles[:]:
                puddle.update(dt)
                if puddle.remove:
                    self.puddles.remove(puddle)
            self.update_death(dt)
            self.animate(dt, moving=(self.direction != (0, 0)))
            return

        # Actualizar teletransporte
        self._update_teleport(dt, maze, target)

        # Actualizar charcos propios (lifetime y fade)
        for puddle in self.puddles[:]:
            puddle.update(dt)
            if puddle.remove:
                self.puddles.remove(puddle)
        
        # ===== SISTEMA DE GENERACIÓN DE CHARCOS =====
        # Solo dejar charcos cuando NO está teletransportándose
        if not self.is_teleporting:
            self.puddle_timer -= dt
            if self.puddle_timer <= 0:
                self._create_puddle()
                self.puddle_timer = WaterConfig.PUDDLE_DROP_INTERVAL

        # Si está teletransportando no hacer movimiento normal
        if self.is_teleporting:
            self.animate(dt, moving=False)
            return

        #  Evasion de bombas del jugador con reaction_time 
        if target:
            player_bombs = getattr(target, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

        # Movimiento via pathfinding
        if target:
            self.follow_player(maze, target, dt, ignore_bricks=False)
        else:
            self.random_walk(dt)

        self.move(dt, maze)
        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))
    
    def _update_teleport(self, dt, maze, target):
        """Actualiza el sistema de teletransporte."""
        if self.is_teleporting:
            # Actualizar animación de teletransporte
            self.teleport_animation_timer += dt
            
            if self.teleport_phase == 'out':
                # Fase de desaparición
                if self.teleport_animation_timer >= WaterConfig.TELEPORT_ANIMATION_TIME:
                    # Cambiar a fase de aparición
                    self._teleport_to_target(maze)
                    self.teleport_phase = 'in'
                    self.teleport_animation_timer = 0.0
                    self.change_animation('teleport_in')
            
            elif self.teleport_phase == 'in':
                # Fase de aparición
                if self.teleport_animation_timer >= WaterConfig.TELEPORT_ANIMATION_TIME:
                    # Teletransporte completado
                    self.is_teleporting = False
                    self.teleport_phase = None
                    self.change_animation('down')
        else:
            # Actualizar cooldown
            self.teleport_timer -= dt
            
            # Intentar teletransporte si está listo y hay objetivo
            if self.teleport_timer <= 0 and target:
                self._start_teleport(target, maze)
    
    def _start_teleport(self, target, maze):
        """Inicia el proceso de teletransporte."""
        # Encontrar posición válida cerca del jugador
        target_pos = self._find_teleport_position(target, maze)
        
        if target_pos:
            self.is_teleporting = True
            self.teleport_phase = 'out'
            self.teleport_target = target_pos
            self.teleport_animation_timer = 0.0
            self.teleport_timer = self.teleport_cooldown
            self.change_animation('teleport_out')
    
    def _find_teleport_position(self, target, maze):
        """
        Determina la celda de destino del teletransporte.

        - Distancia <= TELEPORT_CHASE_RANGE: aparece cerca del jugador.
        - Distancia >  TELEPORT_CHASE_RANGE: salta desde su posicion propia.

        Bug #3 fix: se excluyen celdas a menos de MIN_SAFE_DISTANCE del jugador
        para evitar aparecer encima de el y producir dano garantizado.
        """
        MIN_SAFE_DISTANCE = 3   # distancia Manhattan minima al jugador (celdas)

        cs = maze.cell_size
        my_col,  my_row  = pixel_to_grid(self.x,   self.y,   cs)
        tgt_col, tgt_row = pixel_to_grid(target.x, target.y, cs)

        dist_to_player = abs(tgt_row - my_row) + abs(tgt_col - my_col)

        if dist_to_player <= WaterConfig.TELEPORT_CHASE_RANGE:
            center_row, center_col = tgt_row, tgt_col
            min_d = WaterConfig.TELEPORT_MIN_DISTANCE
            max_d = WaterConfig.TELEPORT_MAX_DISTANCE
        else:
            center_row, center_col = my_row, my_col
            min_d = 5
            max_d = 10

        valid = []
        for dr in range(-max_d, max_d + 1):
            for dc in range(-max_d, max_d + 1):
                row, col = center_row + dr, center_col + dc
                d = abs(dr) + abs(dc)
                if d < min_d or d > max_d:
                    continue
                if not (0 < row < maze.rows - 1 and 0 < col < maze.cols - 1):
                    continue
                if maze.grid[row][col] != 'empty':
                    continue

                # Bug #3: no aparecer a menos de MIN_SAFE_DISTANCE del jugador
                dist_from_player = abs(row - tgt_row) + abs(col - tgt_col)
                if dist_from_player < MIN_SAFE_DISTANCE:
                    continue

                x, y = grid_to_pixel(row, col, cs, center=False)
                valid.append((x, y))

        return random.choice(valid) if valid else None
    
    def _teleport_to_target(self, maze):
        """Ejecuta el teletransporte a la posición objetivo."""
        if self.teleport_target:
            self.x, self.y = self.teleport_target
            self.rect.topleft = (self.x, self.y)
            self.teleport_target = None
    
    def _update_puddles(self, dt):
        """Actualiza el sistema de charcos."""
        self.puddle_timer -= dt
        
        # Crear nuevo charco
        if self.puddle_timer <= 0:
            self._create_puddle()
            self.puddle_timer = WaterConfig.PUDDLE_DROP_INTERVAL
    
    def _create_puddle(self):
        """Crea un nuevo charco en la posición actual."""
        from powerups import WaterPuddle
        puddle = WaterPuddle((self.x, self.y))
        self.puddles.append(puddle)
    
    def draw(self, screen, camera):
        """Dibuja Water con efecto de transparencia durante teletransporte."""
        if self.dead:
            super().draw(screen, camera)
            return

        screen_x, screen_y = camera.apply(self.x, self.y)
        zoom = getattr(camera, 'zoom', 1.0)
        img  = self.image
        if zoom != 1.0:
            sw = max(1, int(img.get_width()  * zoom))
            sh = max(1, int(img.get_height() * zoom))
            img = pygame.transform.scale(img, (sw, sh))

        # Alpha segun fase de teletransporte
        alpha = 255
        if self.is_teleporting:
            progress = self.teleport_animation_timer / WaterConfig.TELEPORT_ANIMATION_TIME
            if self.teleport_phase == 'out':
                alpha = int(255 * (1.0 - progress))
            elif self.teleport_phase == 'in':
                alpha = int(255 * progress)

        draw_img = img.copy()
        draw_img.set_alpha(alpha)
        screen.blit(draw_img, (int(screen_x), int(screen_y)))

        # Los charcos se dibujan en game_level.py (capa separada)

        #  Efectos visuales (stun + '!') — siempre visibles 
        if self._kick_stun_timer > 0:
            self._draw_stun_stars(screen, screen_x, screen_y, img, zoom)
        if self._exclamation_timer > 0:
            self._draw_exclamation(screen, screen_x, screen_y, img, zoom)
    
    def _create_puddle(self):
        """Crea un nuevo charco en la posición actual del Water."""
        from powerups import WaterPuddle
        
        # Alinear al grid para que el charco quede centrado en la celda
        cs = CELL_SIZE
        puddle_x = (int(self.x // cs)) * cs
        puddle_y = (int(self.y // cs)) * cs
        
        puddle = WaterPuddle((puddle_x, puddle_y))
        self.puddles.append(puddle)


class Globe(LivingEntity):
    """
    Enemigo Globe que vuela y suelta powerups para otros enemigos.
    
    Habilidades:
    - Se eleva periódicamente (invulnerable mientras vuela)
    - Salta 1 bloque cuando está elevado
    - Suelta powerups que benefician a enemigos
    - Genera sombra cuando está en el aire
    """
    
    def __init__(self, pos):
        # Configuración de animaciones
        animations_config = {
            'up':    ['globe.png'],
            'down':  ['globe.png'],
            'left':  ['globe_stand.png', 'globe_move01.png', 'globe_move02.png'],
            'right': ['globe_sta.png',   'globe_m01.png',  'globe_m02.png'],
            'dead':  ['enemy_fall.png', 'enemy_fall01.png', 'enemy_fall02.png', 'enemy_fall03.png'],
            'flying': ['globe_sta.png', 'globe_m01.png', 'globe_m02.png']
        }
        
        animations = load_animations_from_dict(animations_config)
        
        # Inicializar clase base
        super().__init__(
            pos=pos,
            width=32,
            height=32,
            speed=GlobeConfig.SPEED,
            animations=animations,
            lives=GlobeConfig.LIVES,
            detection_range=GlobeConfig.DETECTION_RANGE,
            initial_status='down',
            animation_speed=6
        )
        
        self._bomb_reaction_time = GlobeConfig.BOMB_REACTION_TIME
        self.enemy_type = 'Globe'
        self.score_value = GlobeConfig.SCORE

        # Globe muere al primer impacto de bomba (fuera de vuelo)
        # invincibility_duration=0  no hay i-frames  un hit = muerte
        self.invincibility_duration = 0.0
        
        # Sistema de vuelo
        self.is_flying = False
        self.fly_timer = GlobeConfig.FLY_INTERVAL
        self.fly_duration_timer = 0.0
        self.flight_offset = 0  # Offset vertical visual

        self._descending_to_empty = False
        self._target_landing_pos = None
        self._descent_speed_multiplier = 3.0
        
        # Powerups para enemigos
        self.powerup_timer = GlobeConfig.POWERUP_DROP_INTERVAL
        self.enemy_powerups = []  # Lista de powerups activos
        
        # NUEVO: Sistema de cooldown individual por tipo de powerup
        # NOTA: Los tipos reales son 'speed_boost', 'health_boost', 'armor'
        self.powerup_cooldowns = {
            'health_boost': 0.0,  # Era 'extra_life'
            'speed_boost': 0.0,
            'armor': 0.0          # Era 'shield'
        }
        # Límites activos simultáneos por tipo
        self.active_powerup_limits = {
            'health_boost': 1,  # Solo 1 vida extra a la vez
            'speed_boost': 2,   # Hasta 2 speed boosts
            'armor': 3          # Hasta 3 armors
        }
        # Cooldown después de que se recoge un powerup (segundos)
        self.powerup_cooldown_times = {
            'health_boost': 10.0,  # 10 segundos
            'speed_boost': 10.0,   # 10 segundos
            'armor': 10.0          # 10 segundos
        }
    
    def update(self, dt, maze, target=None, enemies=None):
        """Actualización con vuelo y powerups."""
        if self.dead:
            self.update_death(dt)
            self.animate(dt, moving=False)
            return
        
        # WAIT state check (previene vibración)
        if self.update_wait_state(dt):
            self._update_flight(dt, maze)
            self._update_powerups(dt, enemies)
            self.enemy_powerups = [p for p in self.enemy_powerups if not p.collected]
            self.update_death(dt)
            self.animate(dt, moving=(self.direction != (0, 0)))
            return
        
        if self._descending_to_empty:
            self.direction = (0, 0)
            self._update_flight(dt, maze)
            self.update_death(dt)
            self.animate(dt, moving=True)
            return
        
        self._update_flight(dt, maze)

        # Powerups para enemigos
        self._update_powerups(dt, enemies)
        # Limpiar powerups recogidos de la lista propia
        self.enemy_powerups = [p for p in self.enemy_powerups if not p.collected]

        #  Evasion de bombas del jugador con reaction_time 
        if target:
            player_bombs = getattr(target, 'bombs', [])
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                player_bombs, maze, dt)
            if bomb_threat is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                if self.is_flying:
                    self._move_flying(dt, maze)
                else:
                    self.move(dt, maze)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return

        # Pathfinding (volando ignora bricks)
        if target:
            ignore = self.is_flying
            self.follow_player(maze, target, dt, ignore_bricks=ignore)
        else:
            self.random_walk(dt)

        # Movimiento: volando = sin colisiones, normal = con colisiones
        if self.is_flying:
            self._move_flying(dt, maze)
        else:
            self.move(dt, maze)

        self.update_death(dt)
        self.animate(dt, moving=(self.direction != (0, 0)))
    
    def _update_flight(self, dt, maze=None):
        """
        Actualiza el sistema de vuelo.

        Bug #3 fix: al aterrizar, verificar que la celda sea 'empty'.
        Si Globe esta sobre un bloque al terminar el vuelo, se teletransporta
        a la celda vacia mas cercana antes de activar colisiones normales.
        """
        if self.is_flying:
            self.fly_duration_timer += dt
            progress = min(self.fly_duration_timer / 0.5, 1.0)
            self.flight_offset = int(GlobeConfig.FLY_HEIGHT * progress)

            if self.fly_duration_timer >= GlobeConfig.FLY_DURATION:
                # Verificar que la celda de aterrizaje sea empty (bug #3)
                if maze is not None:
                    cs  = maze.cell_size
                    col = int(self.x // cs)
                    row = int(self.y // cs)

                    # Comprobar si esta fuera del area jugable o en bloque
                    on_block = (
                        row <= 0 or row >= maze.rows - 1 or
                        col <= 0 or col >= maze.cols - 1 or
                        maze.grid[row][col] != 'empty'
                    )
                    if on_block:
                        nearest = self._find_nearest_empty_cell(maze, row, col)
                        if nearest:
                            nr, nc = nearest
                            self.x = nc * cs
                            self.y = nr * cs
                            self.rect.topleft = (self.x, self.y)

                self.is_flying        = False
                self.fly_duration_timer = 0.0
                self.flight_offset    = 0
                self.fly_timer        = GlobeConfig.FLY_INTERVAL
                self.change_animation('down')
        else:
            self.fly_timer -= dt
            if self.fly_timer <= 0:
                self.is_flying          = True
                self.fly_duration_timer = 0.0
                self.change_animation('flying')

    def _find_nearest_empty_cell(self, maze, start_row, start_col):
        """
        BFS para encontrar la celda 'empty' mas cercana al punto dado.

        Returns:
            (row, col) o None
        """
        from collections import deque
        visited = set()
        queue   = deque([(start_row, start_col)])
        visited.add((start_row, start_col))

        while queue:
            r, c = queue.popleft()
            if (0 < r < maze.rows - 1 and 0 < c < maze.cols - 1 and
                    maze.grid[r][c] == 'empty'):
                return (r, c)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) not in visited and 0 <= nr < maze.rows and 0 <= nc < maze.cols:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return None
    
    def _move_flying(self, dt, maze):
        """Movimiento especial cuando está volando (puede saltar sobre bloques)."""
        if self.direction == (0, 0):
            return
        
        # Calcular siguiente posición
        move_x = self.direction[0] * self.speed * dt
        move_y = self.direction[1] * self.speed * dt
        
        next_x = self.x + move_x
        next_y = self.y + move_y
        
        # Verificar límites del mapa
        if next_x < 0 or next_x + self.width > maze.width:
            return
        if next_y < 0 or next_y + self.height > maze.height:
            return
        
        # Cuando vuela, puede pasar sobre todo (excepto límites)
        self.x = next_x
        self.y = next_y
        self.rect.topleft = (self.x, self.y)
    
    def _update_powerups(self, dt, enemies):
        """
        Suelta powerups y los aplica a enemigos NO Globe.
        También hace tick de timers de aura/speed de todos los enemigos.
        
        NUEVO: Sistema de cooldown individual por tipo de powerup
        """
        # Actualizar cooldowns de powerups
        for ptype in self.powerup_cooldowns:
            if self.powerup_cooldowns[ptype] > 0:
                self.powerup_cooldowns[ptype] -= dt
        
        self.powerup_timer -= dt
        if self.powerup_timer <= 0:
            self._create_enemy_powerup()
            self.powerup_timer = GlobeConfig.POWERUP_DROP_INTERVAL

        # ── Tick timers de powerup ──
        if enemies:
            for e in enemies:
                aura_t = getattr(e, '_powerup_aura_timer', 0)
                if aura_t > 0:
                    e._powerup_aura_timer = aura_t - dt
                    if e._powerup_aura_timer <= 0:
                        e.active_powerup = None
                spd_t = getattr(e, '_speed_boost_timer', 0)
                if spd_t > 0:
                    e._speed_boost_timer = spd_t - dt
                    if e._speed_boost_timer <= 0:
                        if hasattr(e, '_base_speed'):
                            e.speed = e._base_speed
                            del e._base_speed

        # ── Aplicar powerups solo a enemigos NO Globe ──
        if enemies:
            for powerup in self.enemy_powerups:
                if powerup.collected:
                    continue
                for enemy in enemies:
                    if enemy.enemy_type == 'Globe':
                        continue
                    if enemy.dead:
                        continue
                    if enemy.rect.colliderect(powerup.rect):
                        powerup.apply_to_enemy(enemy)
                        # Activar cooldown cuando se recoge
                        ptype = powerup.type  # CORREGIDO: es .type, no .powerup_type
                        if ptype in self.powerup_cooldowns:
                            self.powerup_cooldowns[ptype] = self.powerup_cooldown_times[ptype]
                        break
    
    def _create_enemy_powerup(self):
        """
        Crea un powerup para enemigos.
        
        NUEVO: Puede no crear nada si todos los tipos están en cooldown/límite
        """
        from powerups import EnemyPowerup
        # Elegir tipo aleatorio (puede ser None si no hay disponibles)
        powerup_type = self._choose_powerup_type()
        
        # No crear powerup si no hay tipos disponibles
        if powerup_type is None:
            return
        
        powerup = EnemyPowerup((self.x, self.y), powerup_type)
        self.enemy_powerups.append(powerup)
    
    def _choose_powerup_type(self):
        """
        Elige un tipo de powerup según probabilidades.
        
        NUEVO: Respeta cooldowns y límites activos
        """
        # Contar cuántos powerups activos hay de cada tipo
        active_counts = {
            'health_boost': 0,
            'speed_boost': 0,
            'armor': 0
        }
        
        for powerup in self.enemy_powerups:
            if not powerup.collected:
                ptype = powerup.type  # CORREGIDO: es .type, no .powerup_type
                if ptype in active_counts:
                    active_counts[ptype] += 1
        
        # Crear lista de tipos disponibles (no en cooldown y no al límite)
        available_types = {}
        for ptype, prob in GlobeConfig.POWERUP_TYPES.itemás():
            # Verificar cooldown
            if self.powerup_cooldowns.get(ptype, 0) > 0:
                continue
            
            # Verificar límite activo
            if active_counts.get(ptype, 0) >= self.active_powerup_limits.get(ptype, 999):
                continue
            
            available_types[ptype] = prob
        
        # Si no hay tipos disponibles, retornar None (no crear powerup)
        if not available_types:
            return None
        
        # Normalizar probabilidades
        total_prob = sum(available_types.values())
        normalized = {k: v/total_prob for k, v in available_types.itemás()}
        
        # Elegir según probabilidad normalizada
        rand = random.random()
        cumulative = 0.0
        
        for ptype, prob in normalized.itemás():
            cumulative += prob
            if rand <= cumulative:
                return ptype
        
        # Fallback (no debería llegar aquí)
        return list(available_types.keys())[0] if available_types else None
        return 'speed_boost'  # Fallback
    
    def take_damage(self, amount):
        """Override: No recibe daño mientras vuela."""
        if self.is_flying:
            return False
        return super().take_damage(amount)
    
    def draw(self, screen, camera):
        """Dibuja Globe con sombra cuando esta volando."""
        if self.dead:
            super().draw(screen, camera)
            return

        screen_x, screen_y = camera.apply(self.x, self.y)
        zoom = getattr(camera, 'zoom', 1.0)
        img  = self.image
        if zoom != 1.0:
            sw = max(1, int(img.get_width()  * zoom))
            sh = max(1, int(img.get_height() * zoom))
            img = pygame.transform.scale(img, (sw, sh))

        # Sombra si está volando
        if self.is_flying and self.flight_offset > 0:
            shadow_surf = pygame.Surface((img.get_width(), img.get_height() // 4), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, GlobeConfig.SHADOW_ALPHA))
            screen.blit(shadow_surf, (int(screen_x), int(screen_y + img.get_height() - 8)))

        # Globe con offset de vuelo
        image_y = screen_y - self.flight_offset
        screen.blit(img, (int(screen_x), int(image_y)))

        # Powerups
        for powerup in self.enemy_powerups:
            if not powerup.collected:
                powerup.draw(screen, camera)

        #  Efectos visuales (stun + '!') 
        # Usar position sin flight_offset para que aparezcan sobre el sprite real
        if self._kick_stun_timer > 0:
            self._draw_stun_stars(screen, screen_x, image_y, img, zoom)
        if self._exclamation_timer > 0:
            self._draw_exclamation(screen, screen_x, image_y, img, zoom)