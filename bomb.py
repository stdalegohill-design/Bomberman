"""
Sistema de bombas con explosión, pateo y física de empuje.

Este módulo implementa la clase Bomb y clases relacionadas para el sistema
completo de bombas del juego. Incluye temporizador, cálculo de explosión
en cruz, pateo (kick) con física, empuje de jugadores y sistema per-player
de colisión para multiplayer.

Clases Exportadas:
    - Bomb: Bomba con temporizador, explosión y pateo
    - GPSBomb: Bomba inteligente que persigue al jugador (Robot)
    - Explosion: Representación visual de explosión
    - SnowTile: Baldosa de hielo dejada por Snow
    - PuddleTile: Charco dejado por Water
    - EnemyPowerup: Powerup especial de Globe

Características Principales:
    - Temporizador configurable (default 3 segundos)
    - Explosión en patrón de cruz con rango variable
    - Pateo (kick) con física y empuje de jugadores
    - Sistema per-player para colisión en multiplayer
    - Bombas GPS con pathfinding propio
    - Cooldown de pateo para evitar spam

Uso Típico:
    # Colocar bomba
    bomb = Bomb(
        pos=(player.x, player.y),
        owner_id=player.player_id,
        explosion_range=player.bomb_range
    )
    
    # En game loop
    bomb.update(dt, maze, players)
    
    # Verificar explosión
    if bomb.exploded:
        damage_rects = bomb.explosion_rects

Notas de Implementación:
    - El patrón de explosión considera obstáculos (detiene en muro)
    - Los ladrillos bloquean pero son destruidos
    - El pateo usa cooldown de 300ms para evitar spam
    - El sistema per-player permite empujar bombas entre jugadores
    - Las bombas GPS persiguen con pathfinding A*
"""


import pygame
import math
from entities import AnimatedEntity, load_animations_from_dict
from settings import BombConfig, CELL_SIZE


class Bomb(AnimatedEntity):
    """
    Bomba colocada por Bomberman.

    Features:
    - Timer con explosión automática
    - Cálculo de rango de explosión
    - Sistema de pateo (kick)
    - Animación heredada de AnimatedEntity
    """

    def __init__(self, pos, sprite_prefix='', owner_id=None):
        # sprite_prefix='' para jugador, 'robot_' para Robot
        p = sprite_prefix
        # Configuración de animaciones
        animations_config = {
            'ticking': [f'{p}bomb.png', f'{p}bomb01.png', f'{p}bomb02.png'],
            'explosion': ['boom.png', 'boom01.png', 'boom02.png', 'boom03.png'],
            'flame_horizontal': ['exp_der.png', 'exp_der01.png', 'exp_der02.png', 'exp_der03.png'],
            'flame_vertical': ['exp_up.png', 'exp_up01.png', 'exp_up02.png', 'exp_up03.png'],
            'flame_end_right': ['der_exp.png', 'der_exp01.png', 'der_exp02.png', 'der_exp03.png'],
            'flame_end_left': ['izq_exp.png', 'izq_exp01.png', 'izq_exp02.png', 'izq_exp03.png'],
            'flame_end_up': ['up_exp.png', 'up_exp01.png', 'up_exp02.png', 'up_exp03.png'],
            'flame_end_down': ['down_exp.png', 'down_exp01.png', 'down_exp02.png', 'down_exp03.png']
        }

        animations = load_animations_from_dict(animations_config)

        super().__init__(
            animations=animations,
            initial_status='ticking',
            animation_speed=BombConfig.ANIMATION_SPEED
        )

        self.x, self.y = pos
        self.width = BombConfig.SIZE
        self.height = BombConfig.SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Timer
        self.timer = BombConfig.FUSE_TIME
        self.exploded = False

        # Explosión
        self.explosion_range = BombConfig.BASE_RANGE
        self.explosion_rects = []
        self.explosion_pos = None

        # Pateo
        self.can_be_kicked = False
        self.is_being_kicked = False
        self.kick_direction = (0, 0)
        self.kick_speed = BombConfig.KICK_SPEED
        self.kick_distance = 0
        self.max_kick_distance = BombConfig.MAX_KICK_DISTANCE

        # Colisión con jugador
        self.can_collide_with_player = False
        
        # Sistema de ownership para multiplayer
        self.owner_id = owner_id
        
        # Sistema de colision per-player (multiplayer)
        # Diccionario: {player_id: puede_colisionar}
        self._can_collide_per_player = {}
        
        # Cooldown de pateo para evitar re-pateo infinito
        self._kick_cooldown = 0.0
        self._kick_cooldown_duration = 0.3  # 300más
        
        # NUEVO: Bomba como obstáculo sólido
        self.is_solid = False  # Se activa cuando jugador/robot sale de la celda
        
        # NUEVO: Sistema de empuje (cuando otra bomba la golpea)
        self.is_being_pushed = False
        self.push_direction = (0, 0)
        self.push_speed = BombConfig.KICK_SPEED * 0.5  # Mitad de velocidad del kick
        self.push_distance = 0
        self.max_push_distance = CELL_SIZE  # 1 celda de distancia máxima
        
        self.remove = False
        # True si esta bomba es de Robot (no daña a aliados enemigos)
        self._robot_owner = (sprite_prefix == 'robot_')
        # Garantiza que los daños de UNA explosión se aplican solo una vez
        self.hits_applied = False

    # TIMER Y EXPLOSIÓN

    def update_timer(self, dt):
        """Cuenta regresiva de la bomba."""
        if not self.exploded:
            self.timer -= dt
            if self.timer <= 0:
                self.trigger_explosion()

    def trigger_explosion(self):
        """Activa la explosión."""
        if not self.exploded:
            self.exploded = True
            self.change_animation('explosion')
            self.explosion_pos = (self.x, self.y)

    def calculate_explosion(self, maze):
        """
        Calcula los rectángulos de explosión en todas las direcciones.
        Solo se ejecuta una vez (hits_applied lo garantiza en game_level).

        Args:
            maze: Instancia del laberinto

        Returns:
            List[(rect, direction, is_end)]
        """
        self.explosion_rects = []

        center_col = int(self.x // maze.cell_size)
        center_row = int(self.y // maze.cell_size)

        # Centro
        center_rect = pygame.Rect(
            center_col * maze.cell_size,
            center_row * maze.cell_size,
            maze.cell_size,
            maze.cell_size
        )
        self.explosion_rects.append((center_rect, 'center', False))

        # Las 4 direcciones
        directions = [
            (0, -1, 'up'),
            (0, 1, 'down'),
            (-1, 0, 'left'),
            (1, 0, 'right')
        ]

        for dx, dy, direction in directions:
            for distance in range(1, self.explosion_range + 1):
                target_col = center_col + dx * distance
                target_row = center_row + dy * distance

                if not (0 <= target_row < maze.rows and
                        0 <= target_col < maze.cols):
                    break

                cell_type = maze.grid[target_row][target_col]

                flame_rect = pygame.Rect(
                    target_col * maze.cell_size,
                    target_row * maze.cell_size,
                    maze.cell_size,
                    maze.cell_size
                )

                is_end = False
                should_break = False

                if cell_type == 'ironbrick':
                    break
                elif cell_type == 'brick':
                    is_end = True
                    should_break = True
                elif distance == self.explosion_range:
                    is_end = True

                self.explosion_rects.append((flame_rect, direction, is_end))

                if should_break:
                    break

        return self.explosion_rects

    # SISTEMA DE PATEO

    def _bomb_cell(self, cell_size):
        """Celda de la bomba en el grid."""
        return (int(self.y // cell_size), int(self.x // cell_size))

    def _player_cell(self, bomberman, cell_size):
        """Celda actual de Bomberman usando su hitbox real."""
        if hasattr(bomberman, 'hitbox_offset_x'):
            cx = bomberman.x + bomberman.hitbox_offset_x + bomberman.width // 2
            cy = bomberman.y + bomberman.hitbox_offset_y + bomberman.height // 2
        else:
            cx = bomberman.x + bomberman.width // 2
            cy = bomberman.y + bomberman.height // 2
        return (int(cy // cell_size), int(cx // cell_size))

    def check_player_exit(self, bomberman, cell_size=32):
        """
        DEPRECATED: Mantener por compatibilidad.
        Usar check_all_players_exit() para multiplayer.
        """
        # Llamar al sistema nuevo con lista de 1 jugador
        if bomberman:
            self.check_all_players_exit([bomberman], cell_size)
    
    def check_all_players_exit(self, all_players, cell_size=32):
        """
        Sistema per-player de colision para multiplayer.
        
        Cada jugador tiene su propio estado de colision.
        La bomba se vuelve solida cuando CUALQUIER jugador sale.
        """
        if not all_players:
            return
        
        bomb_cell = self._bomb_cell(cell_size)
        
        # Activar is_solid cuando CUALQUIER jugador sale
        if not self.is_solid:
            for player in all_players:
                player_cell = self._player_cell(player, cell_size)
                if player_cell != bomb_cell:
                    self.is_solid = True
                    break
        
        # Activar can_be_kicked cuando el OWNER sale
        if not self.can_be_kicked:
            # No activar si es bomba GPS
            if getattr(self, '_gps_break_bomb', False):
                return
            
            owner = self._find_owner(all_players)
            if owner:
                owner_cell = self._player_cell(owner, cell_size)
                if owner_cell != bomb_cell:
                    self.can_be_kicked = True
        
        # Verificar colision per-player
        bomb_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for player in all_players:
            player_id = getattr(player, 'player_id', id(player))
            
            # Inicializar estado de este jugador si no existe
            if player_id not in self._can_collide_per_player:
                self._can_collide_per_player[player_id] = False
            
            # Si ya puede colisionar, no hacer nada
            if self._can_collide_per_player[player_id]:
                continue
            
            # Construir rect del jugador
            if hasattr(player, 'hitbox_offset_x'):
                player_rect = pygame.Rect(
                    player.x + player.hitbox_offset_x,
                    player.y + player.hitbox_offset_y,
                    player.width,
                    player.height
                )
            else:
                player_rect = pygame.Rect(player.x, player.y, 
                                         player.width, player.height)
            
            # Activar colision cuando ya no se tocan
            if not player_rect.colliderect(bomb_rect):
                self._can_collide_per_player[player_id] = True
    
    def _find_owner(self, all_players):
        """Encuentra el owner de la bomba en la lista de jugadores."""
        if not hasattr(self, 'owner_id') or self.owner_id is None:
            return all_players[0] if all_players else None
        
        for player in all_players:
            if getattr(player, 'player_id', None) == self.owner_id:
                return player
        
        return None
    
    def can_collide_with(self, player):
        """Verifica si esta bomba puede colisionar con un jugador especifico."""
        player_id = getattr(player, 'player_id', id(player))
        return self._can_collide_per_player.get(player_id, False)

    def try_kick(self, bomberman, cell_size=32):
        """
        Intenta patear. La condición es que Bomberman está en la celda
        adyacente a la bomba moviéndose hacia ella, o acaba de entrar
        en su celda.

        CORREGIDO: No permitir pateo de bombas GPS

        Returns:
            bool: True si la bomba fue pateada
        """
        # Verificación adicional: bomba GPS nunca puede ser pateada
        if getattr(self, '_gps_break_bomb', False):
            return False
        
        if (not self.can_be_kicked or
                self.is_being_kicked or
                self.status == 'explosion' or
                bomberman.direction == (0, 0)):
            return False

        bomb_cell = self._bomb_cell(cell_size)
        player_cell = self._player_cell(bomberman, cell_size)

        # Patear si Bomberman llega a la celda de la bomba
        if player_cell == bomb_cell:
            self.kick_direction = bomberman.direction
            self.is_being_kicked = True
            self.kick_distance = 0
            # NUEVO: Resetear colisión para permitir atravesar mientras se mueve
            self.can_collide_with_player = False
            return True

        # También patear si está en la celda adyacente en la dirección de movimiento
        dr = bomberman.direction[1]
        dc = bomberman.direction[0]
        adjacent = (player_cell[0] + dr, player_cell[1] + dc)
        if adjacent == bomb_cell:
            self.kick_direction = bomberman.direction
            self.is_being_kicked = True
            self.kick_distance = 0
            # NUEVO: Resetear colisión
            self.can_collide_with_player = False
            return True

        return False

    def check_kick_collision(self, player, maze):
        """
        Verifica colision con CUALQUIER jugador para pateo (multiplayer).
        
        NUEVO: Cooldown de 300más para evitar re-pateo infinito.
        
        A diferencia de try_kick, este metodo funciona con cualquier jugador,
        no solo el owner de la bomba. Esto permite que en multiplayer cualquier
        jugador pueda patear cualquier bomba.
        
        Args:
            player: Jugador que podria patear (puede ser diferente al owner)
            maze: Mapa
            
        Returns:
            bool: True si se pateo la bomba
        """
        # Verificacion adicional: bomba GPS nunca puede ser pateada
        if getattr(self, '_gps_break_bomb', False):
            return False
        
        # Verificar cooldown de pateo
        if self._kick_cooldown > 0:
            return False
        
        # Solo patear si la bomba es solida y puede colisionar
        if not self.is_solid or not self.can_be_kicked:
            return False
        
        # Si ya esta siendo pateada, no volver a patear
        if self.is_being_kicked or self.status == 'explosion':
            return False
        
        # El jugador debe estar moviéndose
        if player.direction == (0, 0):
            return False
        
        cs = maze.cell_size
        bomb_cell = self._bomb_cell(cs)
        player_cell = self._player_cell(player, cs)
        
        # Opcion 1: Jugador en la misma celda que la bomba
        if player_cell == bomb_cell:
            self.kick_direction = player.direction
            self.is_being_kicked = True
            self.kick_distance = 0
            self.can_collide_with_player = False
            return True
        
        # Opcion 2: Jugador en celda adyacente moviéndose hacia la bomba
        dr = player.direction[1]
        dc = player.direction[0]
        adjacent = (player_cell[0] + dr, player_cell[1] + dc)
        
        if adjacent == bomb_cell:
            self.kick_direction = player.direction
            self.is_being_kicked = True
            self.kick_distance = 0
            self.can_collide_with_player = False
            self._kick_cooldown = self._kick_cooldown_duration  # Activar cooldown
            return True
        
        return False


    def update_kick_movement(self, dt, maze, players=None, other_bombs=None, enemies=None):
        """
        Actualiza el movimiento de la bomba mientras es pateada.

        Detecta colisión con otras bombas Y con enemigos.
        Si impacta un enemigo: se detiene + aturde al enemigo.

        Args:
            dt         : Delta time
            maze       : Instancia del laberinto
            other_bombs: Lista de otras bombas (para colisión bomba-bomba)
            enemies    : Lista de enemigos vivos (para stun por impacto)
        """
        if not self.is_being_kicked:
            return

        # Calcular próxima posición
        move_x = self.kick_direction[0] * self.kick_speed * dt
        move_y = self.kick_direction[1] * self.kick_speed * dt

        next_x = self.x + move_x
        next_y = self.y + move_y

        next_rect = pygame.Rect(next_x, next_y, self.width, self.height)

        # Raycasting predictivo - Resolucion de colision con jugadores
        # IMPORTANTE: Solo empujar, NO detener aún (enemigos tienen prioridad)
        if players:
            for player in players:
                if getattr(player, 'dead', False):
                    continue
                
                # Construir rect del jugador con hitbox
                if hasattr(player, 'hitbox_offset_x'):
                    player_rect = pygame.Rect(
                        player.x + player.hitbox_offset_x,
                        player.y + player.hitbox_offset_y,
                        player.width,
                        player.height
                    )
                else:
                    player_rect = pygame.Rect(player.x, player.y, 
                                             player.width, player.height)
                
                # Si va a colisionar, intentar empujar jugador
                if next_rect.colliderect(player_rect):
                    pushed = self._try_push_player(player, maze)
                    
                    # Si no se pudo empujar, la bomba seguira moviendose
                    # hasta chocar con enemigo o muro (abajo)
                    # NO hacer return aqui - continuar verificando

        #  Colisión con enemigos (bomba pateada / en movimiento) 
        # PRIORIDAD: Enemigos DETIENEN la bomba (no se empujan)
        if enemies:
            for enemy in enemies:
                if getattr(enemy, 'dead', False):
                    continue
                
                enemy_rect = pygame.Rect(enemy.x, enemy.y,
                                         enemy.width, enemy.height)
                
                if next_rect.colliderect(enemy_rect):
                    # DETENER bomba - enemigos NO se empujan
                    self.stop_kick(maze)
                    
                    # Aturdir al enemigo
                    stun_dur = BombConfig.KICK_STUN_DURATION
                    if hasattr(enemy, 'stun'):
                        enemy.stun(stun_dur)
                    
                    # Efecto visual especial
                    enemy._kick_stun_timer = stun_dur
                    
                    print(f"[BOMB] Colision con {getattr(enemy, 'enemy_type', 'enemy')}: Aturdir {stun_dur}s")
                    return

        #  Colisión con otras bombas 
        if other_bombs:
            for other in other_bombs:
                if other is self:
                    continue
                if not other.is_solid or other.exploded:
                    continue
                
                # NUEVO: Robot no puede empujar bombas del jugador
                # Pero jugador SÍ puede empujar bombas de Robot
                if self._robot_owner and not other._robot_owner:
                    # Bomba de Robot intentando empujar bomba de jugador  BLOQUEAR
                    self.stop_kick(maze)
                    return
                
                other_rect = pygame.Rect(other.x, other.y, other.width, other.height)
                if next_rect.colliderect(other_rect):
                    push_dir = self.kick_direction
                    self.stop_kick(maze)
                    other.start_push(push_dir)
                    return

        # Verificar si algun jugador esta bloqueado (no pudo ser empujado)
        # Esto solo importa si NO chocamos con enemigo arriba
        if players:
            for player in players:
                if getattr(player, 'dead', False):
                    continue
                
                player_rect = pygame.Rect(
                    player.x + getattr(player, 'hitbox_offset_x', 0),
                    player.y + getattr(player, 'hitbox_offset_y', 0),
                    player.width,
                    player.height
                )
                
                if next_rect.colliderect(player_rect):
                    # Jugador sigue en el camino - intentamos empujar pero fallo
                    # DETENER bomba
                    self.stop_kick(maze)
                    return
    
        # Colisión con paredes
        if maze.check_collision_with_blocks(next_rect):
            self.stop_kick(maze)
            return

        # Límites del mapa
        if (next_x < 0 or next_x + self.width > maze.width or
                next_y < 0 or next_y + self.height > maze.height):
            self.stop_kick(maze)
            return

        self.x = next_x
        self.y = next_y
        self.rect.topleft = (self.x, self.y)

        self.kick_distance += math.sqrt(move_x ** 2 + move_y ** 2)

        if self.kick_distance >= self.max_kick_distance:
            self.stop_kick(maze)

    def stop_kick(self, maze):
        """
        Detiene el pateo y alinea al grid.
        
        NUEVO: Reactiva colisión cuando la bomba se detiene
        """
        grid_x = round(self.x / maze.cell_size) * maze.cell_size
        grid_y = round(self.y / maze.cell_size) * maze.cell_size

        self.x = grid_x
        self.y = grid_y
        self.rect.topleft = (self.x, self.y)

        self.is_being_kicked = False
        self.kick_direction = (0, 0)
        self.kick_distance = 0
        
        # NUEVO: Reactivar colisión cuando se detiene
        self.can_collide_with_player = True

    # NUEVO: SISTEMA DE COLISIÓN BOMBA-BOMBA
    

    def _try_push_player(self, player, maze):
        """
        Intenta empujar al jugador fuera del camino de la bomba.
        
        Returns:
            bool: True si se pudo empujar, False si esta bloqueado
        """
        cs = maze.cell_size
        
        # Calcular donde quedaria el jugador empujado (1 celda)
        push_x = player.x + (self.kick_direction[0] * cs)
        push_y = player.y + (self.kick_direction[1] * cs)
        
        # Verificar si esa posicion esta libre
        if hasattr(player, 'hitbox_offset_x'):
            test_rect = pygame.Rect(
                push_x + player.hitbox_offset_x,
                push_y + player.hitbox_offset_y,
                player.width,
                player.height
            )
        else:
            test_rect = pygame.Rect(push_x, push_y, player.width, player.height)
        
        # Verificar colision con bloques
        if maze.check_collision_with_blocks(test_rect):
            return False  # Hay muro, no se puede empujar
        
        # Verificar limites del mapa
        max_x = maze.width - (player.width if not hasattr(player, 'hitbox_offset_x') 
                             else player.width + player.hitbox_offset_x)
        max_y = maze.height - (player.height if not hasattr(player, 'hitbox_offset_y')
                              else player.height + player.hitbox_offset_y)
        
        if push_x < 0 or push_x > max_x or push_y < 0 or push_y > max_y:
            return False  # Fuera del mapa
        
        # EMPUJAR JUGADOR (prioridad jugador > bomba)
        player.x = push_x
        player.y = push_y
        
        # Actualizar rect del jugador si existe
        if hasattr(player, 'rect'):
            if hasattr(player, 'hitbox_offset_x'):
                player.rect.topleft = (
                    player.x + player.hitbox_offset_x,
                    player.y + player.hitbox_offset_y
                )
            else:
                player.rect.topleft = (player.x, player.y)
        
        return True  # Empuje exitoso

    def _check_player_space_behind(self, player, maze, push_direction):
        """
        Verifica si el jugador tiene espacio libre en la direccion de empuje.
        
        Raycasting predictivo: calcula donde quedaria el jugador si es empujado
        y verifica si esa posicion colisionaria con muros.
        
        Args:
            player: Jugador que seria empujado
            maze: Mapa del nivel
            push_direction: Direccion del empuje (dx, dy)
            
        Returns:
            bool: True si hay espacio libre, False si colisionaria con muro
        """
        push_distance = maze.cell_size
        
        future_x = player.x + (push_direction[0] * push_distance)
        future_y = player.y + (push_direction[1] * push_distance)
        
        future_player_rect = pygame.Rect(
            future_x, 
            future_y, 
            player.width, 
            player.height
        )
        
        if maze.check_collision_with_blocks(future_player_rect):
            return False
        
        if (future_x < 0 or future_x + player.width > maze.width or
            future_y < 0 or future_y + player.height > maze.height):
            return False
        
        return True


    def check_bomb_collision(self, other_bombs, cell_size=32):
        """
        Verifica si esta bomba (siendo pateada) choca con otra bomba.
        
        Args:
            other_bombs: Lista de otras bombas en el nivel
            cell_size: Tamaño de celda
        
        Returns:
            Bomb o None: Bomba con la que chocó, o None
        """
        if not self.is_being_kicked:
            return None
        
        my_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for other in other_bombs:
            if other is self:
                continue
            
            # Solo colisionar con bombas sólidas
            if not other.is_solid:
                continue
            
            # Ignorar bombas que ya explotaron
            if other.exploded:
                continue
            
            other_rect = pygame.Rect(other.x, other.y, other.width, other.height)
            
            if my_rect.colliderect(other_rect):
                return other
        
        return None
    
    # NUEVO: SISTEMA DE EMPUJE
    
    def start_push(self, direction):
        """
        Inicia el empuje de la bomba por impacto de otra bomba.
        
        Args:
            direction: (dx, dy) dirección del empuje
        """
        # Validar dirección
        if direction == (0, 0):
            return
        
        if self.is_being_kicked or self.is_being_pushed:
            return  # Ya está en movimiento
        
        if self.exploded:
            return  # No empujar bombas que ya explotaron
        
        if not self.is_solid:
            return  # Solo empujar bombas sólidas
        
        self.is_being_pushed = True
        self.push_direction = direction
        self.push_distance = 0
        # Resetear colisión temporal para permitir movimiento
        self.can_collide_with_player = False
    
    def update_push_movement(self, dt, maze, other_bombs=None, enemies=None):
        """
        Actualiza el movimiento de empuje (similar a kick pero mas lento y corto).
        También aturde enemigos al impactar (con menor duración que el kick).

        Args:
            dt         : Delta time
            maze       : Instancia del laberinto
            other_bombs: Lista de otras bombas
            enemies    : Lista de enemigos vivos
        """
        if not self.is_being_pushed:
            return

        #  Colisión con enemigos durante empuje 
        if enemies:
            move_x = self.push_direction[0] * self.push_speed * dt
            move_y = self.push_direction[1] * self.push_speed * dt
            test_r = pygame.Rect(self.x + move_x, self.y + move_y,
                                 self.width, self.height)
            for enemy in enemies:
                if getattr(enemy, 'dead', False):
                    continue
                er = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                if test_r.colliderect(er):
                    self.stop_push(maze)
                    stun_dur = BombConfig.KICK_STUN_DURATION * 0.6
                    enemy.stun(stun_dur)
                    enemy._kick_stun_timer = stun_dur
                    return

        #  Colisión con otras bombas 
        if other_bombs:
            # Temporalmente simular next position para verificar colisión
            move_x = self.push_direction[0] * self.push_speed * dt
            move_y = self.push_direction[1] * self.push_speed * dt
            test_rect = pygame.Rect(self.x + move_x, self.y + move_y, self.width, self.height)
            
            for other in other_bombs:
                if other is self or not other.is_solid or other.exploded:
                    continue
                other_rect = pygame.Rect(other.x, other.y, other.width, other.height)
                if test_rect.colliderect(other_rect):
                    # Detener empuje sin empujar más (evita cadena infinita)
                    self.stop_push(maze)
                    return
        
        move_x = self.push_direction[0] * self.push_speed * dt
        move_y = self.push_direction[1] * self.push_speed * dt
        
        next_x = self.x + move_x
        next_y = self.y + move_y
        
        next_rect = pygame.Rect(next_x, next_y, self.width, self.height)
        
        # Colisión con paredes
        if maze.check_collision_with_blocks(next_rect):
            self.stop_push(maze)
            return
        
        # Límites del mapa
        if (next_x < 0 or next_x + self.width > maze.width or
                next_y < 0 or next_y + self.height > maze.height):
            self.stop_push(maze)
            return
        
        self.x = next_x
        self.y = next_y
        self.rect.topleft = (self.x, self.y)
        
        self.push_distance += math.sqrt(move_x ** 2 + move_y ** 2)
        
        if self.push_distance >= self.max_push_distance:
            self.stop_push(maze)
    
    def stop_push(self, maze):
        """
        Detiene el empuje y alinea al grid.
        
        NUEVO: Reactiva colisión cuando se detiene
        """
        grid_x = round(self.x / maze.cell_size) * maze.cell_size
        grid_y = round(self.y / maze.cell_size) * maze.cell_size
        
        self.x = grid_x
        self.y = grid_y
        self.rect.topleft = (self.x, self.y)
        
        self.is_being_pushed = False
        self.push_direction = (0, 0)
        self.push_distance = 0
        
        # NUEVO: Reactivar colisión
        self.can_collide_with_player = True

    # ANIMACIÓN (Override de AnimatedEntity)

    def animate(self, dt):
        """Override: la bomba siempre anima (no depende de movimiento)."""
        current_animation = self.animations[self.status]
        self.frame_index += self.animation_speed * dt

        if self.frame_index >= len(current_animation):
            if self.status == 'explosion':
                self.frame_index = len(current_animation) - 1
                self.remove = True
            else:
                self.frame_index = 0

        frame_idx = max(0, min(int(self.frame_index), len(current_animation) - 1))
        self.image = current_animation[frame_idx]

    # DRAW

    def draw(self, screen, camera):
        """Dibuja la bomba y sus efectos visuales (con soporte de zoom)."""
        zoom = getattr(camera, 'zoom', 1.0)
        cs = max(1, int(32 * zoom))   # tamaño de celda escalado

        if self.status == 'ticking':
            screen_x, screen_y = camera.apply(self.x, self.y)
            img = self.image
            if zoom != 1.0:
                img = pygame.transform.scale(img, (cs, cs))
            screen.blit(img, (int(screen_x), int(screen_y)))

            if self.is_being_kicked:
                for i in range(3):
                    offset = (i + 1) * int(10 * zoom)
                    trail_x = self.x - self.kick_direction[0] * (i + 1) * 10
                    trail_y = self.y - self.kick_direction[1] * (i + 1) * 10
                    tx, ty = camera.apply(trail_x, trail_y)
                    trail_surf = pygame.Surface((cs, cs))
                    trail_surf.set_alpha(100 - i * 30)
                    trail_surf.fill((255, 200, 100))
                    screen.blit(trail_surf, (int(tx), int(ty)))

                for i in range(2):
                    lo = (i + 1) * int(8 * zoom)
                    lsx = screen_x + cs // 2 - self.kick_direction[0] * lo
                    lsy = screen_y + cs // 2 - self.kick_direction[1] * lo
                    lex = lsx - self.kick_direction[0] * int(15 * zoom)
                    ley = lsy - self.kick_direction[1] * int(15 * zoom)
                    pygame.draw.line(screen, (255, 255, 100),
                                     (int(lsx), int(lsy)), (int(lex), int(ley)), 2)

            elif self.can_be_kicked:
                pygame.draw.circle(screen, (100, 255, 100),
                                   (int(screen_x + cs - 4), int(screen_y + 4)), 4)

        elif self.status == 'explosion':
            for explosion_data in self.explosion_rects:
                explosion_rect, direction, is_end = explosion_data
                screen_x, screen_y = camera.apply(explosion_rect.x, explosion_rect.y)

                if direction == 'center':
                    anim = self.animations['explosion']
                elif is_end:
                    anim = self.animations[f'flame_end_{direction}']
                else:
                    anim = self.animations['flame_horizontal' if direction in ('left', 'right')
                                           else 'flame_vertical']

                frame_idx = max(0, min(int(self.frame_index), len(anim) - 1))
                frame = anim[frame_idx]
                if zoom != 1.0:
                    frame = pygame.transform.scale(frame, (cs, cs))
                screen.blit(frame, (int(screen_x), int(screen_y)))

    # UPDATE

    def update(self, dt, maze, bomberman=None, players=None, other_bombs=None, enemies=None):
        """
        Actualización principal de la bomba.
        
        NUEVO: Acepta other_bombs para detectar colisiones bomba-bomba
        
        Args:
            dt: Delta time
            maze: Instancia del laberinto
            bomberman: Jugador/Robot (opcional)
            other_bombs: Lista de otras bombas (opcional, para colisiones)
        """
        # Solo actualizar timer si no está en movimiento
        if not self.is_being_kicked and not self.is_being_pushed:
            self.update_timer(dt)

        if self.exploded and not self.explosion_rects:
            self.calculate_explosion(maze)

        if bomberman:
            cs = maze.cell_size
            self.check_player_exit(bomberman, cs)

            if not self.is_being_kicked and not self.is_being_pushed:
                self.try_kick(bomberman, cs)

        # ACTUALIZADO: Pasar other_bombs al update de kick
        if self.is_being_kicked:
            self.update_kick_movement(dt, maze, players, other_bombs, enemies)

        # Actualizar empuje (también con enemies para stun)
        if self.is_being_pushed:
            self.update_push_movement(dt, maze, other_bombs, enemies)

        self.animate(dt)