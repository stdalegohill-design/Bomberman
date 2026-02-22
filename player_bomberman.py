"""
PLAYER_BOMBERMAN.PY - Jugador Controlable
==========================================

Jerarquía de herencia:
    AnimatedEntity
     MovableEntity
         PathfindingEntity
             LivingEntity
                 PlayerBomberman

El jugador hereda de LivingEntity, obteniendo todo el sistema de:
- Animación (AnimatedEntity)
- Movimiento y colisiones (MovableEntity)  
- Sistema de vidas y daño (LivingEntity)
No usa PathfindingEntity directamente pero lo tiene en la jerarquía.

Clase:
------

PlayerBomberman(LivingEntity):
    Personaje controlado por el jugador (teclado o gamepad).
    
    Hereda de: LivingEntity
    No tiene clases hijas
    
    Sistema de controles:
    ---------------------
    - Teclado: Flechas/WASD para mover, Espacio para bomba
    - Gamepad: D-pad/joystick para mover, botón A para bomba
    - player_id: Identifica al jugador (1-4 en multiplayer)
    - controls: Config de teclas específica del jugador
    
    Sistema de bombas:
    ------------------
    - bombs: Lista de bombas activas del jugador
    - max_bombs: Cantidad máxima simultánea
    - active_bomb_count: Contador de bombas activas
    - bomb_range: Alcance de explosión (aumenta con powerups)
    
    Atributos principales:
    - score: Puntuación del jugador
    - finish: Si completó el nivel
    - dead: Si está muerto
    - spawn_pos: Posición inicial (para respawn)
    
    Powerups y habilidades:
    -----------------------
    - remote_bombs: Control remoto de bombas
    - bomb_push: Empujar bombas
    - bomb_pass: Atravesar bombas
    - kick_bombs: Patear bombas
    - super_speed: Velocidad extra
    - vest: Protección extra
    
    Estados especiales:
    -------------------
    - is_slowed: Ralentizado por nieve
    - is_slipping: Resbalando en charco
    - slip_direction: Dirección del resbalón
    - invincibility_timer: Tiempo de invencibilidad post-daño
    
    Métodos principales:
    --------------------
    
    Control:
    - handle_input(): Procesa input de teclado/gamepad
    - get_current_speed(): Calcula velocidad con modificadores
    
    Movimiento:
    - move(): Movimiento con colisiones
    - update(): Frame principal (input + movimiento + bombas)
    
    Bombas:
    - place_bomb(): Coloca bomba si tiene disponibles
    - update_bombs(): Actualiza todas las bombas activas
    - trigger_remote_bombs(): Detona bombas con remote
    
    Powerups:
    - apply_powerup(): Aplica efecto de powerup recogido
    - check_snow_slowdown(): Verifica si pisa nieve
    
    Daño y muerte:
    - take_damage(): Recibe daño con invencibilidad
    - die(): Ejecuta muerte (pierde vida o game over)
    - update_death(): Maneja animación de muerte
    - respawn(): Reaparece en spawn si tiene vidas
    
    Renderizado:
    - draw(): Dibuja jugador con indicadores (invencible, etc.)

Configuración:
--------------
- BombermanConfig: Velocidad, vidas, velocidad de animación
- PlayerConfig: Spawns, colores por jugador
- Controls: Mapeo de teclas por jugador

Uso típico:
-----------
    # Cárear jugador
    player = PlayerBomberman(
        player_id=1,
        pos=(32, 32),
        controls=Controls.PLAYER_1
    )
    
    # Cada frame
    keys = pygame.key.get_pressed()
    player.handle_input(keys)
    player.update(dt, maze)
    player.draw(screen, camera)
    
    # Aplicar powerup
    player.apply_powerup('bomb_range')
    
    # Verificar victoria
    if player.finish:
        print("¡Nivel completado!")
"""


import pygame
from entities import LivingEntity, load_animations_from_dict
from settings import BombermanConfig, BombConfig, PlayerConfig, Controls, CELL_SIZE, WaterConfig
from utils import load_image, apply_tint


# HELPER: cargar animaciones por jugador

def _load_player_animations(player_id: int) -> dict:
    """
    Carga las animaciones para un jugador concreto.

    - P1: sin prefijo  (front_stand.png, ...)
    - P2: prefijo red_ (red_front_stand.png, ...)
    - P3/P4: igual que P1; el tinte se aplica en draw()

    Returns:
        Dict de animaciones listo para load_animations_from_dict
    """
    prefix = PlayerConfig.SPRITE_PREFIX.get(player_id, '')

    # Nombre base de los archivos de cada dirección
    base_frames = {
        'down':  [f'{prefix}front_stand.png', f'{prefix}front_m01.png', f'{prefix}front_m02.png'],
        'up':    [f'{prefix}back_stand.png',  f'{prefix}back_m01.png',  f'{prefix}back_m02.png'],
        'left':  [f'{prefix}left_stand.png',  f'{prefix}left_m01.png',  f'{prefix}left_m02.png'],
        'right': [f'{prefix}right_stand.png', f'{prefix}right_m01.png', f'{prefix}right_m02.png'],
        'dead':  [f'{prefix}dead.png', f'{prefix}dead01.png', f'{prefix}dead02.png',
                  f'{prefix}dead03.png', f'{prefix}dead04.png', f'{prefix}dead05.png',
                  f'{prefix}dead06.png'],
    }
    return load_animations_from_dict(base_frames)


# CLASE PRINCIPAL

class PlayerBomberman(LivingEntity):
    """
    Jugador Bomberman genérico.

    Parámetros clave
    ----------------
    player_id : int
        1..4. Determina controles, sprites y color de UI.

    Atributos públicos importantes
    ------------------------------
    self.controls   : clase Controls.PLAYERx  (acceso a UP/DOWN/LEFT/RIGHT/BOMB)
    self.tint       : color RGB o None
    self.ui_color   : color para la UI de este jugador
    self.score      : puntuación acumulada
    self.bombs      : lista de bombas activas
    self.max_bombs  : máximo simultáneo (sube con power-up)
    self.bomb_range : rango de explosión (sube con power-up)
    self.audio      : AudioManager (asignar desde game_level)
    """

    def __init__(self, pos, player_id: int = 1):
        self.player_id = player_id

        # Controles e identidad visual
        self.controls  = Controls.BY_PLAYER.get(player_id, Controls.PLAYER1)
        self.tint      = PlayerConfig.TINTS.get(player_id)
        self.ui_color  = PlayerConfig.UI_COLORS.get(player_id, (255, 255, 255))
        self.label     = PlayerConfig.LABELS.get(player_id, f'P{player_id}')

        # Cargar animaciones (con prefijo correcto)
        animations = _load_player_animations(player_id)

        super().__init__(
            pos=pos,
            width=BombermanConfig.HITBOX_WIDTH,
            height=BombermanConfig.HITBOX_HEIGHT,
            speed=BombermanConfig.BASE_SPEED,
            animations=animations,
            lives=BombermanConfig.STARTING_LIVES,
            detection_range=0,
            initial_status='down',
            animation_speed=BombermanConfig.ANIMATION_SPEED
        )

        # Dimensiones del sprite visual (más grandes que el hitbox)
        self.sprite_width  = BombermanConfig.SPRITE_WIDTH
        self.sprite_height = BombermanConfig.SPRITE_HEIGHT

        # Offset del hitbox centrado dentro del sprite
        self.hitbox_offset_x = BombermanConfig.HITBOX_OFFSET_X
        self.hitbox_offset_y = BombermanConfig.HITBOX_OFFSET_Y

        # Rect de colisión real (con offset)
        self.rect = pygame.Rect(
            self.x + self.hitbox_offset_x,
            self.y + self.hitbox_offset_y,
            self.width,
            self.height
        )

        # Stats heredados
        self.max_lives            = BombermanConfig.MAX_LIVES
        self.invincibility_duration = BombermanConfig.INVINCIBILITY_DURATION
        self.death_duration       = BombermanConfig.DEATH_DURATION

        # Estado de juego
        self.hit    = False   # Marcado externo para recibir daño
        self.finish = False   # True cuando se acabaron las vidas y terminó animación

        # Sistema de bombas
        self.max_bombs         = 2
        self.bomb_range        = BombConfig.BASE_RANGE
        self.bombs             = []
        self.active_bomb_count = 0

        # Estadísticas
        self.score = 0

        # Modificadores de estado
        self.is_slowed = False

        # Audio (asignar desde game_level)
        self.audio = None

        # Sonido de pasos
        self._walk_timer    = 0.0
        self._walk_interval = 0.3

        # Cache de frames con tinte (evita recrear cada frame)
        self._tinted_cache = {}

        # Alinear al grid al nacer
        self._align_to_grid()

    # GRID / ALINEACIÓN

    def _align_to_grid(self):
        """Centra al jugador dentro de la celda más cercana al nacer."""
        cx = self.x + self.hitbox_offset_x + self.width  // 2
        cy = self.y + self.hitbox_offset_y + self.height // 2

        cell_x = cx // CELL_SIZE
        cell_y = cy // CELL_SIZE

        target_cx = cell_x * CELL_SIZE + CELL_SIZE // 2
        target_cy = cell_y * CELL_SIZE + CELL_SIZE // 2

        self.x = target_cx - self.hitbox_offset_x - self.width  // 2
        self.y = target_cy - self.hitbox_offset_y - self.height // 2

        self.rect.topleft = (
            self.x + self.hitbox_offset_x,
            self.y + self.hitbox_offset_y
        )

    # INPUT

    def handle_input(self):
        """Lee el teclado según los controles asignados al player_id."""
        if self.dead:
            self.change_animation('dead')
            self.direction = (0, 0)
            return

        keys = pygame.key.get_pressed()
        c = self.controls
        dx, dy = 0, 0

        if keys[c.LEFT]:
            dx = -1;  self.change_animation('left')
        elif keys[c.RIGHT]:
            dx = 1;   self.change_animation('right')
        elif keys[c.UP]:
            dy = -1;  self.change_animation('up')
        elif keys[c.DOWN]:
            dy = 1;   self.change_animation('down')

        if dx == 0 and dy == 0:
            self.frame_index = 0

        self.direction = (dx, dy)

    # MOVIMIENTO (con hitbox offset)

    def move(self, dt, maze):
        """
        Override: colisiones usan el hitbox centrado.

        Se aplica una resolucion de empuje cuando una bomba pateada
        solapa al jugador, antes de la logica normal de colisiones.
        Esto evita que Bomberman quede atrapado dentro de un bloque.
        """
        speed = self.get_current_speed()

        # Resolver empuje de bomba pateada ANTES de cualquier movimiento.
        # Si una bomba en movimiento solapa al jugador, se le expulsa hacia
        # la celda mas cercana que este libre de bloques.
        self._resolve_kicked_bomb_push(maze)

        next_x = self.x + self.direction[0] * speed * dt
        next_y = self.y + self.direction[1] * speed * dt

        full_rect = pygame.Rect(
            next_x + self.hitbox_offset_x,
            next_y + self.hitbox_offset_y,
            self.width, self.height
        )

        bomb_collision = self._check_solid_bomb_collision(full_rect)

        if maze.check_collision_with_blocks(full_rect) or bomb_collision:
            # Intentar eje horizontal solo
            if self.direction[0] != 0:
                h_rect = pygame.Rect(
                    next_x + self.hitbox_offset_x,
                    self.y + self.hitbox_offset_y,
                    self.width, self.height
                )
                h_bomb_collision = self._check_solid_bomb_collision(h_rect)
                
                if not maze.check_collision_with_blocks(h_rect) and not h_bomb_collision:
                    self.x = next_x
                else:
                    cs = maze.cell_size
                    if self.direction[0] > 0:
                        right = next_x + self.hitbox_offset_x + self.width
                        self.x = (right // cs) * cs - self.hitbox_offset_x - self.width
                    else:
                        left = next_x + self.hitbox_offset_x
                        self.x = (left // cs + 1) * cs - self.hitbox_offset_x

            # Intentar eje vertical solo
            if self.direction[1] != 0:
                v_rect = pygame.Rect(
                    self.x + self.hitbox_offset_x,
                    next_y + self.hitbox_offset_y,
                    self.width, self.height
                )
                v_bomb_collision = self._check_solid_bomb_collision(v_rect)
                
                if not maze.check_collision_with_blocks(v_rect) and not v_bomb_collision:
                    self.y = next_y
                else:
                    cs = maze.cell_size
                    if self.direction[1] > 0:
                        bottom = next_y + self.hitbox_offset_y + self.height
                        self.y = (bottom // cs) * cs - self.hitbox_offset_y - self.height
                    else:
                        top = next_y + self.hitbox_offset_y
                        self.y = (top // cs + 1) * cs - self.hitbox_offset_y
        else:
            self.x = next_x
            self.y = next_y

        self.rect.topleft = (
            self.x + self.hitbox_offset_x,
            self.y + self.hitbox_offset_y
        )
        self.pos = (self.x, self.y)
    
    def _resolve_kicked_bomb_push(self, maze):
        """
        Expulsa al jugador fuera de cualquier bomba pateada o empujada
        que este solapando su hitbox.

        Algoritmo:
        1. Construir la hitbox actual del jugador.
        2. Para cada bomba en movimiento, si solapa al jugador:
           a. Calcular la direccion de empuje opuesta a la bomba.
           b. Intentar desplazar al jugador 1 celda en esa direccion.
           c. Si esa celda tiene bloque, intentar la perpendicular.
           d. Si nada funciona, desplazar hasta el borde de la celda actual.
        3. Nunca colocar al jugador dentro de un bloque.
        """
        cs = maze.cell_size
        hx = self.x + self.hitbox_offset_x
        hy = self.y + self.hitbox_offset_y
        player_rect = pygame.Rect(hx, hy, self.width, self.height)

        all_bombs = list(self.bombs) + list(getattr(self, '_robot_bombs', []))

        for bomb in all_bombs:
            if not (bomb.is_being_kicked or bomb.is_being_pushed):
                continue
            if getattr(bomb, 'exploded', False):
                continue

            bomb_rect = pygame.Rect(bomb.x, bomb.y, bomb.width, bomb.height)
            if not player_rect.colliderect(bomb_rect):
                continue

            # Direccion de la bomba: usamos kick_direction o push_direction
            if bomb.is_being_kicked:
                bdx, bdy = bomb.kick_direction
            else:
                bdx, bdy = bomb.push_direction

            # El jugador debe moverse en la direccion OPUESTA a la bomba
            push_dx, push_dy = -bdx, -bdy

            # Intentar mover al jugador 1 celda completa en esa direccion
            moved = False
            for attempt_dx, attempt_dy in [
                (push_dx, push_dy),           # direccion opuesta principal
                (push_dy, push_dx),           # perpendicular 1
                (-push_dy, -push_dx),         # perpendicular 2
            ]:
                if attempt_dx == 0 and attempt_dy == 0:
                    continue

                # Calcular posicion candidata (1 celda en esa direccion)
                cand_x = self.x + attempt_dx * cs
                cand_y = self.y + attempt_dy * cs

                cand_rect = pygame.Rect(
                    cand_x + self.hitbox_offset_x,
                    cand_y + self.hitbox_offset_y,
                    self.width, self.height
                )

                # Verificar que la celda destino esta libre de bloques
                if not maze.check_collision_with_blocks(cand_rect):
                    # Verificar limites del mapa
                    if (cand_x >= 0 and cand_x + self.width + self.hitbox_offset_x <= maze.width and
                            cand_y >= 0 and cand_y + self.height + self.hitbox_offset_y <= maze.height):
                        self.x = cand_x
                        self.y = cand_y
                        self.rect.topleft = (
                            self.x + self.hitbox_offset_x,
                            self.y + self.hitbox_offset_y
                        )
                        self.pos = (self.x, self.y)
                        moved = True
                        break

            if not moved:
                # Fallback: centrar al jugador en su celda actual.
                # Esto garantiza que nunca quede solapando el bloque.
                col = int((hx + self.width  // 2) // cs)
                row = int((hy + self.height // 2) // cs)
                col = max(1, min(col, maze.cols - 2))
                row = max(1, min(row, maze.rows - 2))

                # Buscar celda propia o adyacente que sea empty
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    tr, tc = row + dr, col + dc
                    if (0 < tr < maze.rows - 1 and 0 < tc < maze.cols - 1 and
                            maze.grid[tr][tc] == 'empty'):
                        self.x = tc * cs - self.hitbox_offset_x
                        self.y = tr * cs - self.hitbox_offset_y
                        self.rect.topleft = (
                            self.x + self.hitbox_offset_x,
                            self.y + self.hitbox_offset_y
                        )
                        self.pos = (self.x, self.y)
                        break

            # Actualizar hitbox para la siguiente iteracion del bucle
            hx = self.x + self.hitbox_offset_x
            hy = self.y + self.hitbox_offset_y
            player_rect = pygame.Rect(hx, hy, self.width, self.height)

    def _check_solid_bomb_collision(self, player_rect):
        """
        Verifica si el jugador colisionaria con bombas solidas.
        
        Usa sistema per-player: cada bomba rastrea por separado
        si puede colisionar con este jugador especifico.

        Returns:
            bool: True si hay colision con bomba solida
        """
        all_bombs = list(self.bombs) + list(getattr(self, '_robot_bombs', []))

        for bomb in all_bombs:
            # Bombas en movimiento siempre colisionan
            if bomb.is_being_kicked or bomb.is_being_pushed:
                bomb_rect = pygame.Rect(bomb.x, bomb.y, bomb.width, bomb.height)
                if player_rect.colliderect(bomb_rect):
                    return True

            # Bombas solidas: verificar sistema per-player
            if not bomb.is_solid or getattr(bomb, 'exploded', False):
                continue

            # Verificar si esta bomba puede colisionar con ESTE jugador
            if not bomb.can_collide_with(self):
                continue

            bomb_rect = pygame.Rect(bomb.x, bomb.y, bomb.width, bomb.height)
            if player_rect.colliderect(bomb_rect):
                return True

        return False

    def get_current_speed(self):
        """Velocidad base, reducida al 50% si está en nieve."""
        return self.speed * (0.5 if self.is_slowed else 1.0)

    # DAÑO / MUERTE / RESPAWN

    def take_damage(self):
        """Override: usa self.hit como señal externa."""
        if self.hit and self.invincibility_timer <= 0:
            self.lives -= 1

            if self.audio:
                self.audio.play_sfx('player_hit')

            if self.lives <= 0:
                self.die()
                if self.audio:
                    self.audio.play_sfx('player_death')
            else:
                self.invincibility_timer = self.invincibility_duration

            self.hit = False

    def update_death(self, dt):
        """Override: respawn si quedan vidas, finish si no."""
        if self.dead:
            self.death_timer += dt
            if self.death_timer >= self.death_duration:
                if self.lives > 0:
                    self.respawn()
                else:
                    self.finish = True
                    self.remove = True

    def respawn(self):
        """Revive en la posición de spawn con invencibilidad."""
        spawn_col, spawn_row = PlayerConfig.SPAWN_OFFSETS.get(
            self.player_id, (1, 2)
        )
        self.x = spawn_col * CELL_SIZE
        self.y = spawn_row * CELL_SIZE
        self._align_to_grid()

        self.dead          = False
        self.death_timer   = 0.0
        self.remove        = False
        self.direction     = (0, 0)
        self.invincibility_timer = self.invincibility_duration
        self.change_animation('down')

    def reset(self, pos=None):
        """Reinicia completamente (nuevo nivel / restart)."""
        if pos is None:
            spawn_col, spawn_row = PlayerConfig.SPAWN_OFFSETS.get(
                self.player_id, (1, 2)
            )
            pos = (spawn_col * CELL_SIZE, spawn_row * CELL_SIZE)

        self.x, self.y = pos
        self._align_to_grid()

        self.lives             = BombermanConfig.STARTING_LIVES
        self.max_lives         = BombermanConfig.MAX_LIVES
        self.score             = 0
        self.dead              = False
        self.hit               = False
        self.remove            = False
        self.finish            = False
        self.direction         = (0, 0)
        self.invincibility_timer = 0
        self.death_timer       = 0

        self.bombs             = []
        self.active_bomb_count = 0
        self.max_bombs         = 2
        self.bomb_range        = BombConfig.BASE_RANGE

        self.is_slowed         = False
        self.change_animation('down')

    # BOMBAS

    def place_bomb(self, dt):
        """Coloca una bomba si no se superó el máximo permitido."""
        keys = pygame.key.get_pressed()

        if not (keys[self.controls.BOMB] and
                not self.dead and
                self.active_bomb_count < self.max_bombs):
            return

        from bomb import Bomb

        cx = self.x + self.hitbox_offset_x + self.width  // 2
        cy = self.y + self.hitbox_offset_y + self.height // 2

        grid_x = (cx // CELL_SIZE) * CELL_SIZE
        grid_y = (cy // CELL_SIZE) * CELL_SIZE

        # No colocar dos bombas en la misma celda
        new_cell = (grid_y // CELL_SIZE, grid_x // CELL_SIZE)
        for b in self.bombs:
            if (int(b.y // CELL_SIZE), int(b.x // CELL_SIZE)) == new_cell:
                return

        bomb = Bomb((grid_x, grid_y), owner_id=self.player_id)
        bomb.explosion_range = self.bomb_range
        self.bombs.append(bomb)
        self.active_bomb_count += 1

        if self.audio:
            self.audio.play_sfx('bomb_place')

    def update_bombs(self, dt, maze, all_players=None):
        """
        Actualiza las bombas activas; elimina las que terminaron.
        Pasa other_bombs y enemies para colisión bomba-bomba y stun de enemigos.
        """
        other_bombs_list = getattr(self, '_other_bombs', None)
        enemies_list     = getattr(self, '_level_enemies', None)

        for bomb in self.bombs[:]:
            if other_bombs_list:
                other_bombs = [b for b in other_bombs_list if b is not bomb]
            else:
                other_bombs = None

            bomb.update(dt, maze, self, all_players, other_bombs, enemies_list)
            if bomb.remove:
                self.bombs.remove(bomb)
                self.active_bomb_count = max(0, self.active_bomb_count - 1)

    # POWER-UPS

    def check_snow_slowdown(self, snow_tiles):
        """Activa ralentización si está sobre una casilla de nieve."""
        self.is_slowed = any(
            self.rect.colliderect(snow.rect) for snow in snow_tiles
        )
    
    def _check_puddle_collision(self, puddle):
        """Verifica colisión de jugadores con charcos."""
        for player in self.players:
            if player.dead or player.invincibility_timer > 0:
                continue

            from settings import WaterConfig

            if player.rect.colliderect(puddle.rect):
            # Hacer resbalar al jugador
                if not hasattr(player, 'is_slipping'):
                    player.is_slipping = True
                    player.slip_timer = WaterConfig.PUDDLE_SLIP_DURATION
                    player.slip_direction = player.direction
                    player.original_speed = player.speed
                    player.speed = WaterConfig.PUDDLE_SLIP_SPEED

    # UPDATE PRINCIPAL

    def update(self, dt, maze):
        self.take_damage()
        self.update_death(dt)

        if not self.dead and not self.finish:
            # ── Resbalón por charco de Water ──
            if getattr(self, 'is_slipping', False):
                self.slip_timer -= dt
                if self.slip_timer <= 0:
                    self.is_slipping = False
                    self.speed       = self.original_speed
                    self.direction   = (0, 0)
                else:
                    # Bloquear input, forzar dirección y velocidad de resbalón
                    self.direction  = self.slip_direction
                    saved_speed     = self.speed
                    self.speed      = WaterConfig.PUDDLE_SLIP_SPEED
                    self.move(dt, maze)
                    self.speed      = saved_speed
                    self.place_bomb(dt)
                    self.update_bombs(dt, maze)
            else:
                self.handle_input()
                self.move(dt, maze)
                self.place_bomb(dt)
                self.update_bombs(dt, maze)

        if self.invincibility_timer > 0:
            self.invincibility_timer -= dt

        # Sonido de pasos
        if self.direction != (0, 0) and not self.dead:
            self._walk_timer += dt
            if self._walk_timer >= self._walk_interval:
                self._walk_timer = 0.0
                if self.audio:
                    self.audio.play_sfx('walking')
        else:
            self._walk_timer = 0.0

        self.animate(dt, moving=(self.direction != (0, 0)))

    # DRAW (con tinte y parpadeo de i-frames)

    def _get_tinted_image(self):
        """
        Retorna el frame actual con tinte aplicado.
        Usa cache por (status, frame_index) para no recrear cada frame.
        """
        if self.tint is None or self.image is None:
            return self.image

        key = (self.status, self.frame_index)
        if key not in self._tinted_cache:
            self._tinted_cache[key] = apply_tint(self.image, self.tint)
        return self._tinted_cache[key]

    def draw(self, screen, camera):
        """
        Dibuja el sprite con tinte, zoom y parpadeo de i-frames.
        """
        img = self._get_tinted_image()
        if img is None:
            return

        screen_x, screen_y = camera.apply(self.x, self.y)

        # Escalar según el zoom de la cámara
        zoom = getattr(camera, 'zoom', 1.0)
        if zoom != 1.0:
            sw = max(1, int(img.get_width()  * zoom))
            sh = max(1, int(img.get_height() * zoom))
            img = pygame.transform.scale(img, (sw, sh))

        # Parpadeo de i-frames
        if self.invincibility_timer > 0:
            if int(self.invincibility_timer * 10) % 2 == 0:
                screen.blit(img, (int(screen_x), int(screen_y)))
        else:
            screen.blit(img, (int(screen_x), int(screen_y)))

        # Etiqueta P1/P2/... encima del sprite (solo si hay más de 1 jugador)
        if hasattr(self, '_font') and self._font and self.player_id > 0:
            label_surf = self._font.render(self.label, True, self.ui_color)
            sw_lbl = int(self.sprite_width * zoom)
            lx = int(screen_x) + sw_lbl // 2 - label_surf.get_width() // 2
            ly = int(screen_y) - label_surf.get_height() - 2
            screen.blit(label_surf, (lx, ly))

    def set_font(self, font):
        """Asigna la fuente para la etiqueta P1/P2. Llamar desde game_level."""
        self._font = font