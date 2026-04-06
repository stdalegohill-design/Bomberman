"""
Jerarquía de clases base para entidades del juego.

Este módulo implementa la jerarquía OOP completa que elimina duplicación
de código entre jugadores y enemigos. Cada nivel de herencia añade una
capa de funcionalidad: animación, física, IA y sistema de vidas.

La arquitectura sigue un diseño por composición de responsabilidades donde
cada clase agrega exactamente una funcionalidad nueva sobre su padre.

Jerarquía Completa:
    pygame.sprite.Sprite (Pygame base)
        AnimatedEntity: Gestión de animaciones por frames
            MovableEntity: Física y movimiento básico
                PathfindingEntity: IA con A*, detección y evasión
                    LivingEntity: Sistema de vidas, daño e invencibilidad

Clases Exportadas:
    - AnimatedEntity: Base para cualquier sprite animado
    - MovableEntity: Entidad con física y colisiones
    - PathfindingEntity: Entidad con IA y navegación
    - LivingEntity: Entidad completa con sistema de vida/muerte

Clases que Heredan de LivingEntity:
    - PlayerBomberman: Jugador controlado por teclado
    - Ghost, Snow, Bear, Robot, Water, Globe: Enemigos con IA
    - Barrel: Enemigo estático destructible

Uso Típico:
    # Crear nuevo tipo de enemigo
    class NewEnemy(LivingEntity):
        def __init__(self, pos):
            animations = load_animations_from_dict({
                'idle': ['enemy_1.png', 'enemy_2.png'],
                'dead': ['enemy_dead.png']
            })
            super().__init__(
                pos=pos,
                width=32, height=32,
                speed=80,
                animations=animations,
                lives=1,
                detection_range=5
            )
        
        def update(self, dt, maze, target):
            if not self.dead:
                self.follow_player(target, maze)
            super().update(dt)

Notas de Implementación:
    - PathfindingEntity usa A* con heurística Manhattan
    - El sistema de evasión incluye anti-vibración (estado WAIT)
    - La invencibilidad usa i-frames con efecto de parpadeo
    - Todas las entidades usan el mismo sistema de colisión del maze
"""


import pygame
import heapq
import random
from settings import CELL_SIZE, EnemyConfig
from utils import load_image


# CLASE BASE: ANIMACIÓN

class AnimatedEntity:
    """
    Clase base para entidades con animación.
    
    Elimina código repetitivo de animación en Bomberman, Bomb y Enemigos.
    """
    
    def __init__(self, animations, initial_status='down', animation_speed=5):
        """
        Args:
            animations: Dict con {status: [frame1, frame2, ...]}
            initial_status: Estado inicial de animación
            animation_speed: Velocidad de animación (frames/segundo)
        """
        self.animations = animations
        self.status = initial_status
        self.frame_index = 0.0
        self.animation_speed = animation_speed
        
        # Imagen actual
        if self.status in self.animations and len(self.animations[self.status]) > 0:
            self.image = self.animations[self.status][0]
        else:
            self.image = None
    
    def animate(self, dt, moving=False):
        """
        Actualiza la animación.
        
        Args:
            dt: Delta time
            moving: Si True, anima; si False, muestra frame 0
        """
        if self.status not in self.animations:
            return
        
        current_animation = self.animations[self.status]
        
        if len(current_animation) == 0:
            return
        
        # Solo animar si está en movimiento o es un estado especial
        if moving or self.status in ('dead', 'explosion', 'ticking'):
            self.frame_index += self.animation_speed * dt
            
            # Loop o detener en último frame
            if self.frame_index >= len(current_animation):
                if self.status in ('dead', 'explosion'):
                    # Detener en último frame
                    self.frame_index = len(current_animation) - 1
                else:
                    # Loop
                    self.frame_index = 0
        else:
            # No se mueve: mostrar frame 0
            self.frame_index = 0
        
        # Protección de índice
        frame_idx = int(self.frame_index)
        frame_idx = max(0, min(frame_idx, len(current_animation) - 1))
        
        self.image = current_animation[frame_idx]
    
    def change_animation(self, new_status):
        """
        Cambia el estado de animación.
        
        Args:
            new_status: Nuevo estado (debe existir en self.animations)
        """
        if new_status != self.status and new_status in self.animations:
            self.status = new_status
            self.frame_index = 0.0


# CLASE BASE: MOVIMIENTO

class MovableEntity(AnimatedEntity):
    """
    Clase base para entidades que se mueven.
    
    Maneja:
    - Posición y rect
    - Dirección y velocidad
    - Colisiones con el mapa
    - Límites del mapa
    """
    
    def __init__(self, pos, width, height, speed, animations, 
                 initial_status='down', animation_speed=5):
        """
        Args:
            pos: Tupla (x, y)
            width, height: Dimensiones
            speed: Velocidad en píxeles/segundo
            animations: Dict de animaciones
            initial_status: Estado inicial
            animation_speed: Velocidad de animación
        """
        super().__init__(animations, initial_status, animation_speed)
        
        self.x, self.y = pos
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.speed = speed
        self.direction = (0, 0)
        self.pos = (self.x, self.y)
    
    def move(self, dt, maze, ignore_collisions=False):
        """
        Mueve la entidad respetando colisiones.
        
        Args:
            dt: Delta time
            maze: Instancia del laberinto
            ignore_collisions: Si True, ignora paredes (para Ghost mode)
        
        Returns:
            bool: True si hubo colisión
        """
        # Calcular siguiente posición
        next_x = self.x + self.direction[0] * self.speed * dt
        next_y = self.y + self.direction[1] * self.speed * dt
        
        # Límites del mapa
        next_x = max(0, min(next_x, maze.width - self.width))
        next_y = max(0, min(next_y, maze.height - self.height))
        
        # Modo sin colisiones (ej: Ghost)
        if ignore_collisions:
            self.x = next_x
            self.y = next_y
            self.rect.topleft = (self.x, self.y)
            self.pos = (self.x, self.y)
            return False
        
        # Verificar colisiones
        next_rect = pygame.Rect(next_x, next_y, self.width, self.height)
        
        # NUEVO: Verificar colisión con bombas sólidas
        bomb_collision = self._check_bomb_collision(next_rect)
        
        if maze.check_collision_with_blocks(next_rect) or bomb_collision:
            # Si chocó con bomba, marcar para buscar ruta alternativa
            if bomb_collision:
                self._blocked_by_obstacle = True

                # Desencierro: si todas las direcciones están bloqueadas por bombas
                # (no por muros), teleportar a la última posición libre conocida.
                # Esto resuelve el caso donde una bomba se coloca encima del enemigo.
                if hasattr(self, '_last_safe_pos'):
                    all_blocked = True
                    for test_dx, test_dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        test_rect = pygame.Rect(
                            self.x + test_dx * maze.cell_size,
                            self.y + test_dy * maze.cell_size,
                            self.width, self.height
                        )
                        if (not maze.check_collision_with_blocks(test_rect)
                                and not self._check_bomb_collision(test_rect)):
                            all_blocked = False
                            break
                    if all_blocked:
                        # Teleportar a posición segura anterior
                        self.x, self.y = self._last_safe_pos
                        self.rect.topleft = (self.x, self.y)
                        self.pos = (self.x, self.y)
                        return False

            # Alinear al grid en el eje de movimiento.
            # Usamos int() antes de // para evitar errores de punto flotante
            # que dejan al enemigo 1-2px dentro del bloque (causa vibración).
            cs = maze.cell_size
            if self.direction[0] > 0:   # yendo a la derecha → borde izquierdo del bloque
                self.x = (int(next_x) // cs) * cs
            elif self.direction[0] < 0: # yendo a la izquierda → borde derecho del bloque
                self.x = (int(next_x) // cs + 1) * cs

            if self.direction[1] > 0:   # yendo hacia abajo → borde superior del bloque
                self.y = (int(next_y) // cs) * cs
            elif self.direction[1] < 0: # yendo hacia arriba → borde inferior del bloque
                self.y = (int(next_y) // cs + 1) * cs

            # NO reseteamos direction aquí: follow_player la áreasigna cada frame.
            # Si reseteamos, el enemigo queda quieto 1 frame entre cada celda
            # y en giros parece "trabado". Solo resetear en random_walk.
            self.rect.topleft = (self.x, self.y)
            self.pos = (self.x, self.y)
            return True  # Hubo colisión
        else:
            # Movimiento libre — actualizar última posición segura
            self._blocked_by_bomb = False
            self.x = next_x
            self.y = next_y
            self.rect.topleft = (self.x, self.y)
            self.pos = (self.x, self.y)
            if hasattr(self, '_last_safe_pos'):
                self._last_safe_pos = (self.x, self.y)
            return False
    
    def _check_bomb_collision(self, entity_rect):
        """
        Verifica si el enemigo colisionaría con bombas sólidas.
        Ignora las bombas propias del enemigo (ej: bombas del Robot)
        para que pueda alejarse después de colocarlas.
        """
        all_bombs = getattr(self, '_all_bombs', [])
        own_bombs = set(getattr(self, 'bombs', []))  # bombas propias a ignorar

        for bomb in all_bombs:
            if bomb in own_bombs:
                continue   # ignorar propias — igual que el jugador ignora las suyas
            if not bomb.is_solid:
                continue
            if bomb.exploded:
                continue
            bomb_rect = pygame.Rect(bomb.x, bomb.y, bomb.width, bomb.height)
            if entity_rect.colliderect(bomb_rect):
                return True

        return False
    
    def random_walk(self, dt):
        """
        Movimiento aleatorio mejorado (anti-vibracion).

        Cambios:
        - Camina en una direccion durante 1-3 segundos.
        - Si choca con una bomba (_blocked_by_bomb=True), fuerza el cambio
          de direccion inmediatamente para evitar la vibracion frame a frame.
        - Si la nueva direccion elegida tambien esta bloqueada en el proximo
          frame, el ciclo de forzado garantiza que encuentre una libre.
        - 20% de probabilidad de quedarse quieto (idle natural).

        Args:
            dt: Delta time
        """
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return

        self._walk_timer += dt

        # Forzar cambio de direccion inmediato si chocamos con bomba
        blocked_by_bomb = getattr(self, '_blocked_by_bomb', False)

        if self._walk_timer >= self._walk_duration or blocked_by_bomb:
            self._walk_timer    = 0.0
            self._walk_duration = random.uniform(1.0, 3.0)

            choices = ['up', 'down', 'left', 'right', 'idle']
            weights = [20, 20, 20, 20, 20]

            # Si estamos bloqueados por bomba, excluir idle y priorizar escape
            if blocked_by_bomb:
                choices = ['up', 'down', 'left', 'right']
                weights = [25, 25, 25, 25]
                self._blocked_by_bomb = False  # Reset flag

            new_status = random.choices(choices, weights=weights)[0]

            if new_status == 'idle':
                self.direction = (0, 0)
            else:
                direction_map = {
                    'up':    (0, -1),
                    'down':  (0,  1),
                    'left':  (-1, 0),
                    'right': ( 1, 0)
                }
                self.direction = direction_map[new_status]
                self.change_animation(new_status)


# CLASE BASE: PATHFINDING

class PathfindingEntity(MovableEntity):
    """
    Clase base para entidades con pathfinding A*.
    
    Maneja:
    - Búsqueda de caminos A*
    - Seguimiento de jugador
    - Navegación inteligente
    """
    
    def __init__(self, pos, width, height, speed, animations, 
                 detection_range=5, initial_status='down', animation_speed=5):
        """
        Args:
            pos: Tupla (x, y)
            width, height: Dimensiones
            speed: Velocidad
            animations: Dict de animaciones
            detection_range: Rango de detección en celdas
            initial_status: Estado inicial
            animation_speed: Velocidad de animación
        """
        super().__init__(pos, width, height, speed, animations, 
                        initial_status, animation_speed)
        
        self.detection_range = detection_range
        self.movement_timer = 0.0
        # Referencia al maze; asignada por game_level antes de cada update.
        # Necesaria para que _nearby_bomb_danger pueda verificar celdas libres.
        self._maze_ref = None
        
        # ===== Sistema de escape inteligente (anti-vibración) =====
        self._escaping_bomb = False           # Flag: está escapando
        self._escape_target_cell = None       # Celda objetivo de escape
        self._escape_committed = False        # Ya eligió celda, no cambiar
        self._safe_from_bomb = False          # Ya está a salvo, quedarse quieto
        self._bomb_being_escaped = None       # Referencia a la bomba
        self._skip_normal_update = False      # Skip actualización normal
        
        # Estado WAIT para prevenir vibración (Bug #2)
        self._in_wait_state = False
        self._wait_timer = 0.0
        self._wait_duration = 0.5          # breve pausa de estabilización post-escape
        self._escape_cooldown = 0.0
        self._escape_cooldown_duration = 0.5  # tiempo mínimo antes de detectar otra bomba
        
        # Random walk mejorado
        self._walk_timer = 0.0
        self._walk_duration = 0.0
        
        # OPTIMIZACIÓN: Caché de pathfinding
        self._path_cache = None
        self._path_cache_goal = None
        self._path_cache_timer = 0.0
        self._path_cache_duration = 0.3  # Recalcular cada 0.3s máximo
    
    def find_path(self, maze, start, goal, ignore_bricks=False):
        """
        A* Pathfinding.
        
        Args:
            maze: Instancia del laberinto
            start: Tupla (row, col)
            goal: Tupla (row, col)
            ignore_bricks: Si True, puede atravesar ladrillos
        
        Returns:
            List[(row, col)]: Camino desde start hasta goal (sin incluir start)
        """
        frontier = []
        heapq.heappush(frontier, (0, start))
        
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while frontier:
            _, current = heapq.heappop(frontier)
            
            if current == goal:
                break
            
            current_row, current_col = current
            
            for dr, dc in neighbors:
                next_node = (current_row + dr, current_col + dc)
                
                # Verificar límites
                if not (0 <= next_node[0] < maze.rows and 
                        0 <= next_node[1] < maze.cols):
                    continue
                
                # Verificar obstáculos
                cell_type = maze.grid[next_node[0]][next_node[1]]
                if cell_type == 'ironbrick':
                    continue
                if cell_type == 'brick' and not ignore_bricks:
                    continue
                
                new_cost = cost_so_far[current] + 1
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    # Heurística Manhattan
                    priority = new_cost + abs(goal[0] - next_node[0]) + abs(goal[1] - next_node[1])
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
        
        # Reconstruir camino
        if goal not in came_from:
            return []
        
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        
        path.reverse()
        return path

    def _path_distance(self, maze, start_cell, goal_cell, ignore_bricks=False):
        """
        Retorna la distancia en celdas del camino A* entre start y goal.
        Si no hay camino (completamente bloqueado), retorna float('inf').
        Usa el mismo A* que find_path para ser 100% consistente.
        """
        path = self.find_path(maze, start_cell, goal_cell, ignore_bricks)
        return len(path) if path else float('inf')

    def _nearby_bomb_danger(self, all_bombs, safety_radius_cells=4):
        """
        Detecta si alguna bomba activa supone peligro inminente y calcula
        la celda de escape más segura Y alcanzable por A*.

        Condiciones de peligro:
        A) Misma fila, dentro del rango, sin muro bloqueante.
        B) Misma columna, dentro del rango, sin muro bloqueante.
        C) Distancia Manhattan ≤ brange (pánico por proximidad: esquinas, entradas).

        La celda de escape elegida garantiza que existe un path A* real,
        previniendo que el enemigo se congele al intentar llegar a una
        celda inaccesible a través de muros.

        Returns:
            (Bomb, (escape_row, escape_col))  si hay peligro
            (None, None)                       si está seguro
        """
        cs     = CELL_SIZE
        my_col = int((self.x + self.width  // 2) // cs)
        my_row = int((self.y + self.height // 2) // cs)
        maze   = self._maze_ref

        for bomb in all_bombs:
            if getattr(bomb, 'remove', False):
                continue
            if getattr(bomb, 'exploded', False):
                continue

            bomb_col = int(bomb.x // cs)
            bomb_row = int(bomb.y // cs)
            brange   = getattr(bomb, 'explosion_range', 2)

            # ── Condiciones de peligro ───────────────────────────────────────
            in_blast_row = (my_row == bomb_row and abs(my_col - bomb_col) <= brange)
            in_blast_col = (my_col == bomb_col and abs(my_row - bomb_row) <= brange)
            near_center  = (abs(my_row - bomb_row) + abs(my_col - bomb_col)) <= max(1, brange - 1)

            in_danger = False
            if in_blast_row or in_blast_col:
                if not (maze and self._wall_blocks_explosion(
                        my_row, my_col, bomb_row, bomb_col, maze)):
                    in_danger = True
            elif near_center:
                in_danger = True

            if not in_danger:
                continue

            # ── Recopilar candidatos de escape ───────────────────────────────
            search_r  = brange + 2
            candidates = []   # (dist_from_bomb, (er, ec))

            for dr in range(-search_r, search_r + 1):
                for dc in range(-search_r, search_r + 1):
                    er, ec = my_row + dr, my_col + dc
                    if maze is not None:
                        if not (0 < er < maze.rows - 1 and 0 < ec < maze.cols - 1):
                            continue
                        if maze.grid[er][ec] in ('ironbrick', 'brick'):
                            continue

                    # Descartar celdas en línea de fuego sin muro protector
                    cand_in_row = (er == bomb_row and abs(ec - bomb_col) <= brange)
                    cand_in_col = (ec == bomb_col and abs(er - bomb_row) <= brange)
                    if cand_in_row or cand_in_col:
                        if not (maze and self._wall_blocks_explosion(
                                er, ec, bomb_row, bomb_col, maze)):
                            continue   # en blast sin protección — no válida

                    dist_from_bomb = abs(er - bomb_row) + abs(ec - bomb_col)
                    candidates.append((dist_from_bomb, (er, ec)))

            if not candidates:
                continue

            # Ordenar de más a menos alejado de la bomba
            candidates.sort(reverse=True)

            # Verificar alcanzabilidad A* para los mejores candidatos.
            # Solo comprobamos los top N para no hundir el rendimiento.
            MAX_VERIFY = 6
            for dist_val, cell in candidates[:MAX_VERIFY]:
                if maze is None:
                    return bomb, cell   # sin maze: confiar en Manhattan
                path = self.find_path(maze, (my_row, my_col), cell)
                if path:
                    return bomb, cell   # encontrado: alcanzable

            # Ninguno de los top-N tiene path — devolver el más lejano sin
            # verificar (el enemigo al menos se moverá en alguna dirección).
            if candidates:
                return bomb, candidates[0][1]

        return None, None
    
    def smart_bomb_escape(self, bomb, escape_cell, maze, dt):
        """
        Escape inteligente de bombas.

        1. Primera vez: registrar celda de escape y comprometerse.
        2. Moverse hacia esa celda usando A* (no solo un paso).
        3. Al llegar: verificar seguridad.
           - Segura  → quedarse quieto hasta que la bomba explote/desaparezca.
           - No segura → buscar una celda más lejana y continuar.
        4. Bomba explotó/desapareció → resetear estado.

        Returns:
            bool: True si está manejando el escape (no hacer nada más).
        """
        cs     = maze.cell_size
        cx     = self.x + self.width  // 2
        cy     = self.y + self.height // 2
        my_col = int(cx // cs)
        my_row = int(cy // cs)

        # Primera vez escapando de esta bomba
        if not self._escaping_bomb:
            self._escaping_bomb      = True
            self._escape_target_cell = escape_cell
            self._safe_from_bomb     = False
            self._bomb_being_escaped = bomb

        # Bomba desapareció o explotó → terminar escape
        if getattr(bomb, 'remove', False) or getattr(bomb, 'exploded', False):
            self._reset_escape_state()
            return False

        # Ya llegamos y estamos seguros: quietos
        if self._safe_from_bomb:
            self.direction = (0, 0)
            return True

        # Llegamos a la celda comprometida — verificar si es segura
        if (my_row, my_col) == self._escape_target_cell:
            if self._is_safe_from_explosion(bomb, maze):
                self._safe_from_bomb = True
                self.direction = (0, 0)
                return True
            else:
                # Celda no segura (rango de bomba grande).
                # Buscar la celda más alejada posible usando A*
                # para asegurarnos de que sea alcanzable.
                bomb_col = int(bomb.x // cs)
                bomb_row = int(bomb.y // cs)
                brange   = getattr(bomb, 'explosion_range', 2)
                search_r = brange + 3

                best_cell = None
                best_dist = -1
                for dr in range(-search_r, search_r + 1):
                    for dc in range(-search_r, search_r + 1):
                        er, ec = my_row + dr, my_col + dc
                        if not (0 < er < maze.rows-1 and 0 < ec < maze.cols-1):
                            continue
                        if maze.grid[er][ec] in ('ironbrick', 'brick'):
                            continue
                        if (er, ec) == (my_row, my_col):
                            continue
                        # Verificar que sea genuinamente segura
                        in_br = (er == bomb_row and abs(ec - bomb_col) <= brange)
                        in_bc = (ec == bomb_col and abs(er - bomb_row) <= brange)
                        if in_br or in_bc:
                            if not self._wall_blocks_explosion(
                                    er, ec, bomb_row, bomb_col, maze):
                                continue
                        # Verificar que hay camino real
                        path = self.find_path(maze, (my_row, my_col), (er, ec))
                        if not path:
                            continue
                        d = abs(er - bomb_row) + abs(ec - bomb_col)
                        if d > best_dist:
                            best_dist = d
                            best_cell = (er, ec)

                if best_cell:
                    self._escape_target_cell = best_cell
                else:
                    # Sin alternativa alcanzable: aceptar posición actual
                    self._safe_from_bomb = True
                    self.direction = (0, 0)
                    return True

        # Moverse hacia la celda de escape usando A*
        target_row, target_col = self._escape_target_cell
        path = self.find_path(maze, (my_row, my_col), (target_row, target_col))
        if path:
            next_step = path[0]
            if next_step == (my_row, my_col) and len(path) > 1:
                next_step = path[1]
            self._move_toward_cell(next_step, maze, dt)
        else:
            # Sin path al target: buscar cualquier celda adyacente libre
            # que se aleje de la bomba en vez de congelarse.
            bomb_col = int(getattr(self._bomb_being_escaped, 'x', 0) // cs)
            bomb_row = int(getattr(self._bomb_being_escaped, 'y', 0) // cs)
            best_adj = None
            best_adj_dist = -1
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                ar, ac = my_row+dr, my_col+dc
                if maze and not (0 < ar < maze.rows-1 and 0 < ac < maze.cols-1):
                    continue
                if maze and maze.grid[ar][ac] in ('ironbrick','brick'):
                    continue
                d = abs(ar - bomb_row) + abs(ac - bomb_col)
                if d > best_adj_dist:
                    best_adj_dist = d
                    best_adj = (ar, ac)
            if best_adj:
                self._escape_target_cell = best_adj
                self._move_toward_cell(best_adj, maze, dt)
            else:
                # Completamente rodeado: quieto (no hay opción)
                self._safe_from_bomb = True
                self.direction = (0, 0)

        return True
    
    def _is_safe_from_explosion(self, bomb, maze):
        """
        Verifica si la posición actual está fuera del alcance de la explosión.
        Usa el centro del sprite para ser consistente con el resto del sistema.
        """
        cs = maze.cell_size
        my_col = int((self.x + self.width  // 2) // cs)
        my_row = int((self.y + self.height // 2) // cs)

        bomb_col  = int(bomb.x // cs)
        bomb_row  = int(bomb.y // cs)
        brange    = getattr(bomb, 'explosion_range', 2)
        
        # Misma fila/columna = peligro si está en rango
        if my_row == bomb_row:
            dist = abs(my_col - bomb_col)
            if dist <= brange:
                if self._wall_blocks_explosion(my_row, my_col, bomb_row, bomb_col, maze):
                    return True
                return False

        if my_col == bomb_col:
            dist = abs(my_row - bomb_row)
            if dist <= brange:
                if self._wall_blocks_explosion(my_row, my_col, bomb_row, bomb_col, maze):
                    return True
                return False

        # Diferente fila y columna = seguro
        return True
    
    def _wall_blocks_explosion(self, my_row, my_col, bomb_row, bomb_col, maze):
        """
        Verifica si hay un muro bloqueando la explosión.
        
        Returns:
            bool: True si hay muro protector
        """
        # Recorrer desde bomba hasta nosotros
        if my_row == bomb_row:
            # Misma fila
            start_col = min(my_col, bomb_col)
            end_col = max(my_col, bomb_col)
            
            for col in range(start_col + 1, end_col):
                cell = maze.grid[my_row][col]
                if cell in ('ironbrick', 'brick'):
                    return True
        
        elif my_col == bomb_col:
            # Misma columna
            start_row = min(my_row, bomb_row)
            end_row = max(my_row, bomb_row)
            
            for row in range(start_row + 1, end_row):
                cell = maze.grid[row][my_col]
                if cell in ('ironbrick', 'brick'):
                    return True
        
        return False
    
    def _reset_escape_state(self):
        """Resetea el estado de escape y entra en WAIT breve."""
        self._escaping_bomb      = False
        self._escape_target_cell = None
        self._escape_committed   = False
        self._safe_from_bomb     = False
        self._bomb_being_escaped = None
        self._bomb_perception_timer = 0.0
        self._bomb_perceived        = False
        self._danger_cache          = (None, None)
        self._danger_cache_timer    = 0.0
        self._in_wait_state   = True
        self._wait_timer      = self._wait_duration
        self._escape_cooldown = self._escape_cooldown_duration

    def update_wait_state(self, dt):
        """
        Actualiza el estado WAIT (espera breve después de escapar de una bomba).
        Durante este estado el enemigo se queda quieto — no camina aleatoriamente,
        lo que podría llevarlo de vuelta al radio de explosión.
        """
        if self._escape_cooldown > 0:
            self._escape_cooldown -= dt

        if not self._in_wait_state:
            return False

        self._wait_timer -= dt

        if self._wait_timer > 0:
            self.direction = (0, 0)   # quieto siempre durante WAIT
            return True

        self._in_wait_state = False
        self._wait_timer    = 0.0
        return False

    def _move_toward_cell(self, target_cell, maze, dt):
        """
        Mueve la entidad hacia el centro de target_cell (row, col).

        Todo se calcula desde el CENTRO del sprite (cx/cy), no desde la
        esquina superior-izquierda. Esto evita que el cálculo de dirección
        cambie antes de que el sprite haya cruzado visualmente la celda.

        Llegada:
        - Si la distancia al centro de destino es < ARRIVE_THRESHOLD px,
          hace snap directo y pone direction=(0,0).  El frame siguiente,
          follow_player recalcula el path desde la celda correcta y avanza
          al próximo paso sin micro-pausa ni oscilación.

        Corrección perpendicular:
        - Mientras se mueve en X, alinea Y al centro de la fila actual.
        - Mientras se mueve en Y, alinea X al centro de la columna actual.
        - Snap inmediato si el desajuste perpendicular es ≤ 1 px.
        """
        ARRIVE_THRESHOLD = 3.0   # px — distancia para considerar celda alcanzada

        cs  = maze.cell_size
        # Centro del sprite
        cx  = self.x + self.width  // 2
        cy  = self.y + self.height // 2

        next_row, next_col = target_cell
        # Centro de la celda destino
        target_cx = next_col * cs + cs // 2
        target_cy = next_row * cs + cs // 2

        dx = target_cx - cx
        dy = target_cy - cy

        # ── Llegada: snap y detener ──────────────────────────────────────────
        if abs(dx) < ARRIVE_THRESHOLD and abs(dy) < ARRIVE_THRESHOLD:
            # Posicionar el sprite exactamente en el centro de la celda
            self.x = target_cx - self.width  // 2
            self.y = target_cy - self.height // 2
            self.direction = (0, 0)
            return

        # ── Movimiento principal + corrección perpendicular ──────────────────
        if abs(dx) >= abs(dy):
            # Eje principal: X
            self.direction = (1 if dx > 0 else -1, 0)
            self.change_animation('right' if dx > 0 else 'left')

            # Corrección perpendicular: centrar en la fila actual
            # Usamos la fila calculada desde el CENTRO del sprite
            my_row       = int(cy // cs)
            row_center_y = my_row * cs + cs // 2 - self.height // 2
            diff_y       = row_center_y - self.y
            if abs(diff_y) <= 1.0:
                self.y = row_center_y
            elif abs(diff_y) > 0.5:
                step   = min(abs(diff_y), self.speed * dt * 0.5)
                self.y += step if diff_y > 0 else -step
        else:
            # Eje principal: Y
            self.direction = (0, 1 if dy > 0 else -1)
            self.change_animation('down' if dy > 0 else 'up')

            # Corrección perpendicular: centrar en la columna actual
            my_col       = int(cx // cs)
            col_center_x = my_col * cs + cs // 2 - self.width // 2
            diff_x       = col_center_x - self.x
            if abs(diff_x) <= 1.0:
                self.x = col_center_x
            elif abs(diff_x) > 0.5:
                step   = min(abs(diff_x), self.speed * dt * 0.5)
                self.x += step if diff_x > 0 else -step

    def follow_player(self, maze, player, dt, ignore_bricks=False,
                      robot_bombs=None):
        """
        Sigue al jugador usando A*.

        Si robot_bombs contiene bombas peligrosas cerca, el enemigo se
        desvía a la celda de escape antes de perseguir. Esto aplica a
        Ghost, Snow, Bear, Barrel y Robot por igual.
        
        NUEVO: Si está bloqueado por bomba, intenta ruta alternativa

        Args:
            maze         : Instancia del laberinto
            player       : Entidad objetivo
            dt           : Delta time
            ignore_bricks: Si True, ignora ladrillos (Bear en sniff)
            robot_bombs  : Lista de Bomb del Robot (para evasión de aliados)
        """
        if self.is_stunned:
            return

        cs = maze.cell_size
        # Calcular la celda desde el CENTRO del sprite para que coincida
        # con _move_toward_cell y no haya cambios de celda prematuros.
        cx = self.x + self.width  // 2
        cy = self.y + self.height // 2
        my_cell = (int(cy // cs), int(cx // cs))

        #  Evasión de bombas peligrosas 
        if robot_bombs:
            bomb, escape_cell = self._nearby_bomb_danger(robot_bombs)
            if bomb is not None and escape_cell is not None:
                self._move_toward_cell(escape_cell, maze, dt)
                return
        # 

        # Si el enemigo esta bloqueado por una bomba, buscar la celda adyacente
        # mas proxima que este libre, para rodear el obstaculo sin vibrar.
        if getattr(self, '_blocked_by_bomb', False):
            self._blocked_by_bomb = False  # Consumir el flag

            if self.direction[0] != 0:
                ordered = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            elif self.direction[1] != 0:
                ordered = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            else:
                ordered = [(-1, 0), (1, 0), (0, -1), (0, 1)]

            anim_map = {(-1, 0): 'left', (1, 0): 'right',
                        (0, -1): 'up',   (0, 1): 'down'}

            for opt_dx, opt_dy in ordered:
                nc = my_cell[1] + opt_dx
                nr = my_cell[0] + opt_dy
                if not (0 < nr < maze.rows - 1 and 0 < nc < maze.cols - 1):
                    continue
                if maze.grid[nr][nc] in ('ironbrick', 'brick'):
                    continue
                test_rect = pygame.Rect(
                    self.x + opt_dx * cs,
                    self.y + opt_dy * cs,
                    self.width, self.height
                )
                if self._check_bomb_collision(test_rect):
                    continue
                self.direction = (opt_dx, opt_dy)
                if (opt_dx, opt_dy) in anim_map:
                    self.change_animation(anim_map[(opt_dx, opt_dy)])
                return

            # Ninguna celda libre: esperar quieto este frame
            self.direction = (0, 0)
            return

        # Celda del jugador (con soporte de hitbox offset de Bomberman)
        if hasattr(player, 'hitbox_offset_x'):
            px = player.x + player.hitbox_offset_x + player.width  // 2
            py = player.y + player.hitbox_offset_y + player.height // 2
        else:
            px = player.x + player.width  // 2
            py = player.y + player.height // 2
        player_cell = (int(py // cs), int(px // cs))

        if my_cell == player_cell:
            return

        # OPTIMIZACIÓN: Usar caché si está disponible y vigente
        self._path_cache_timer += dt

        needs_recalc = (
            self._path_cache is None or
            self._path_cache_goal != player_cell or
            self._path_cache_timer >= self._path_cache_duration
        )

        if needs_recalc:
            path = self.find_path(maze, my_cell, player_cell, ignore_bricks)
            self._path_cache = path
            self._path_cache_goal = player_cell
            self._path_cache_timer = 0.0
        else:
            path = self._path_cache

        # Detección basada en distancia de camino real (no Euclidiana).
        # Si el path supera detection_range celdas, el enemigo no "ve" al jugador
        # aunque esté cerca en línea recta pero separado por muros.
        if not path or len(path) > self.detection_range:
            self.random_walk(dt)
            return

        # Avanzar al siguiente paso del path
        next_step = path[0]
        if next_step == my_cell and len(path) > 1:
            next_step = path[1]
        self._move_toward_cell(next_step, maze, dt)


# CLASE BASE: ENTIDAD CON VIDA

class LivingEntity(PathfindingEntity):
    """
    Clase base para entidades con sistema de vida/muerte.
    
    Maneja:
    - Vidas y daño
    - Invencibilidad temporal
    - Muerte y animación de muerte
    - Remoción
    """
    
    def __init__(self, pos, width, height, speed, animations, lives=1,
                 detection_range=5, initial_status='down', animation_speed=5):
        """
        Args:
            pos: Tupla (x, y)
            width, height: Dimensiones
            speed: Velocidad
            animations: Dict de animaciones
            lives: Vidas iniciales
            detection_range: Rango de detección
            initial_status: Estado inicial
            animation_speed: Velocidad de animación
        """
        super().__init__(pos, width, height, speed, animations, 
                        detection_range, initial_status, animation_speed)
        
        self.lives = lives
        self.max_lives = lives
        
        # Sistema de invencibilidad
        self.invincibility_timer = 0.0
        self.invincibility_duration = EnemyConfig.INVINCIBILITY_DURATION
        
        # Sistema de muerte
        self.dead = False
        self.death_timer = 0.0
        self.death_duration = EnemyConfig.DEATH_DURATION
        self.remove = False

        # Sistema de aturdimiento (stun)
        self.stun_timer       = 0.0
        self._kick_stun_timer = 0.0   # stun por bomba pateada (efecto visual estrellas)

        # Percepcion de bomba del jugador (con retraso segun tipo de enemigo)
        self._bomb_perception_timer = 0.0   # acumulador: tiempo viendo la bomba cercana
        self._bomb_perceived        = False  # ya la percibio -> puede escapar
        self._exclamation_timer     = 0.0   # muestra '!' sobre la cabeza al percibir
        self._bomb_reaction_time     = 1.5   # override en __init__ de cada subclase

        # Powerup activo: None | 'speed_boost' | 'health_boost' | 'armor'
        self.active_powerup      = None
        self._powerup_aura_timer = 0.0
        self._speed_boost_timer  = 0.0
    
    def take_damage(self, damage=1):
        """
        Recibe daño con sistema de i-frames.
        
        Args:
            damage: Cantidad de daño
        """
        if self.invincibility_timer <= 0 and not self.dead:
            self.lives -= damage
            self.invincibility_timer = self.invincibility_duration
            
            if self.lives <= 0:
                self.die()
    
    def die(self):
        """Inicia la animación de muerte."""
        if not self.dead:
            self.dead = True
            self.change_animation('dead')
            self.direction = (0, 0)
    
    def stun(self, duration):
        """
        Aturde a la entidad: no puede moverse ni perseguir durante 'duration' segundos.
        
        Args:
            duration: Segundos de aturdimiento
        """
        self.stun_timer = duration
        self.direction = (0, 0)

    @property
    def is_stunned(self):
        """True si está aturdido."""""
        return self.stun_timer > 0

    def update_death(self, dt):
        """
        Actualiza timers de muerte, invencibilidad y aturdimiento.
        
        Args:
            dt: Delta time
        """
        if self.dead:
            self.death_timer += dt
            if self.death_timer >= self.death_duration:
                self.remove = True

        if self.invincibility_timer > 0:
            self.invincibility_timer -= dt

        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.direction = (0, 0)  # Mantener quieto mientras aturdido

        if self._kick_stun_timer > 0:
            self._kick_stun_timer -= dt

        if self._exclamation_timer > 0:
            self._exclamation_timer -= dt
    
    def check_player_bomb_danger(self, player_bombs, maze, dt, instant=False):
        """
        Detecta si hay una bomba peligrosa cerca, con retraso de percepcion.

        Incluye caché de 0.15s para evitar recalcular A* cada frame cuando
        hay muchas bombas en pantalla (previene congelamiento con múltiples Robots).

        - Si instant=True (ej: Robot), retorna la amenaza inmediatamente.
        - Si instant=False, acumula _bomb_perception_timer hasta reaction_time.

        Returns:
            (Bomb, escape_cell) si debe escapar ahora, (None, None) si no.
        """
        if self._in_wait_state or self._escape_cooldown > 0:
            self._bomb_perception_timer = 0.0
            self._bomb_perceived = False
            self._danger_cache   = (None, None)
            return None, None

        if self.dead or self.is_stunned:
            self._bomb_perception_timer = 0.0
            self._bomb_perceived        = False
            self._danger_cache          = (None, None)
            return None, None

        # ── Caché de detección (evita A* costoso cada frame) ─────────────────
        self._danger_cache_timer += dt
        if (self._danger_cache_timer >= self._danger_cache_duration
                or self._danger_cache == (None, None)):
            bomb_threat, escape_cell = self._nearby_bomb_danger(
                player_bombs, safety_radius_cells=4
            )
            self._danger_cache       = (bomb_threat, escape_cell)
            self._danger_cache_timer = 0.0
        else:
            bomb_threat, escape_cell = self._danger_cache

        if bomb_threat is None:
            self._bomb_perception_timer = 0.0
            self._bomb_perceived        = False
            return None, None

        # Detección instantánea (Robot)
        if instant:
            self._bomb_perceived    = True
            self._exclamation_timer = 0.0
            return bomb_threat, escape_cell

        if self._bomb_perceived:
            return bomb_threat, escape_cell

        self._bomb_perception_timer += dt
        if self._bomb_perception_timer >= self._bomb_reaction_time:
            self._bomb_perceived    = True
            self._exclamation_timer = 1.2
            return bomb_threat, escape_cell

        return None, None

    def _draw_stun_stars(self, screen, screen_x, screen_y, img, zoom):
        """
        Dibuja estrellas giratorias sobre la cabeza del enemigo durante kick-stun.
        Se llama desde draw() de LivingEntity y tambien puede llamarse desde
        draw() custom de Ghost/Globe/Water.
        """
        import math, time
        cx = int(screen_x + img.get_width()  * 0.5)
        cy = int(screen_y - max(5, int(6 * zoom)))
        radius     = max(10, int(13 * zoom))
        star_count = 3
        t_now      = time.time()
        for si in range(star_count):
            angle = t_now * 4.0 + si * (2 * math.pi / star_count)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * radius * 0.55)
            sr = max(3, int(4 * zoom))
            pygame.draw.circle(screen, (60, 30, 0), (sx+1, sy+1), sr)
            col = (255, int(220 + 35 * math.sin(t_now * 8 + si)), 0)
            pygame.draw.circle(screen, col, (sx, sy), sr)
            if sr >= 4:
                pygame.draw.circle(screen, (255, 255, 255), (sx, sy), max(1, sr//2))

    def _draw_exclamation(self, screen, screen_x, screen_y, img, zoom):
        """
        Dibuja un '!' rojo parpadeante sobre la cabeza al percibir una bomba.
        """
        import math, time
        if self._exclamation_timer <= 0:
            return
        cx = int(screen_x + img.get_width() * 0.5)
        cy = int(screen_y - max(8, int(10 * zoom)))
        # Parpadeo rapido
        if int(time.time() * 8) % 2 == 0:
            return
        # Fondo negro pequeño para contraste
        bg_r = max(6, int(7 * zoom))
        pygame.draw.circle(screen, (30, 0, 0), (cx+1, cy+1), bg_r+1)
        pygame.draw.circle(screen, (200, 0, 0), (cx, cy), bg_r+1)
        # Texto '!'  dibujado como formas geometricas (no necesita font)
        bar_w = max(2, int(2 * zoom))
        bar_h = max(6, int(7 * zoom))
        # Barra vertical del !
        pygame.draw.rect(screen, (255, 60, 0),
                         (cx - bar_w//2, cy - bar_h//2 - 1, bar_w, bar_h))
        # Punto del !
        pygame.draw.rect(screen, (255, 200, 0),
                         (cx - bar_w//2, cy + bar_h//2 + 1, bar_w, bar_w))

    # Colores de aura por tipo de powerup
    AURA_COLORS = {
        'speed_boost':  (255, 220,  30),
        'health_boost': (255,  60,  60),
        'armor':        ( 80, 120, 255),
    }

    def draw(self, screen, camera):
        """Dibuja la entidad con aura de powerup y parpadeo de invencibilidad."""
        if not self.image:
            return

        screen_x, screen_y = camera.apply(self.x, self.y)
        zoom = getattr(camera, 'zoom', 1.0)
        img = self.image
        if zoom != 1.0:
            sw = max(1, int(self.image.get_width()  * zoom))
            sh = max(1, int(self.image.get_height() * zoom))
            img = pygame.transform.scale(self.image, (sw, sh))

        #  Aura de powerup (se dibuja ANTES del sprite) 
        active_pu = getattr(self, 'active_powerup', None)
        if active_pu and active_pu in self.AURA_COLORS:
            import math, time
            r, g, b = self.AURA_COLORS[active_pu]
            w, h    = img.get_width(), img.get_height()
            margin  = max(4, int(6 * zoom))
            pulse   = int(70 + 50 * math.sin(time.time() * 6))
            pulse   = max(30, min(160, pulse))
            aura_s  = pygame.Surface((w+margin*2, h+margin*2), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_s, (r, g, b, pulse),
                                (0, 0, w+margin*2, h+margin*2))
            screen.blit(aura_s, (int(screen_x)-margin, int(screen_y)-margin))
            bc = (min(255,r+80), min(255,g+80), min(255,b+80))
            pygame.draw.ellipse(screen, bc,
                                (int(screen_x)-margin, int(screen_y)-margin,
                                 w+margin*2, h+margin*2), 2)

        #  Parpadeo de invencibilidad 
        if self.invincibility_timer > 0:
            if int(self.invincibility_timer * 10) % 2 == 0:
                screen.blit(img, (int(screen_x), int(screen_y)))
        else:
            screen.blit(img, (int(screen_x), int(screen_y)))

        #  Estrellas de kick-stun + signo '!' de percepcion de bomba 
        if self._kick_stun_timer > 0:
            self._draw_stun_stars(screen, screen_x, screen_y, img, zoom)
        if self._exclamation_timer > 0:
            self._draw_exclamation(screen, screen_x, screen_y, img, zoom)


# CEREBRO DE ENEMIGOS

class EnemyBrain(LivingEntity):
    """
    Gestor centralizado de IA para todos los enemigos.

    Se inserta entre LivingEntity y cada enemigo concreto, eliminando el
    código duplicado de evasión, WAIT y toma de decisiones que antes se
    repetía en Ghost, Snow, Bear, Barrel, Water y Globe.

    Jerarquía completa:
        AnimatedEntity → MovableEntity → PathfindingEntity
            → LivingEntity → EnemyBrain → Ghost / Snow / Bear / ...

    Máquina de estados con prioridades fijas
    ─────────────────────────────────────────
    DEAD        Cualquier otra cosa se ignora.
    STUNNED     Quieto; solo corren timers internos.
    ESCAPING    Prioridad total: moverse a escape_cell, esperar explosión.
    WAIT        Post-escape: idle breve para estabilizar posición.
    CHASING     A* hacia el jugador (dentro del detection_range).
    WANDERING   random_walk (fuera de rango o sin target).

    Transiciones
    ─────────────
    • Percibir bomba del jugador (reaction_time) → ESCAPING
    • Bomba desaparece / llegar a celda segura    → WAIT
    • WAIT expira                                 → CHASING / WANDERING
    • Jugador entra en detection_range            → CHASING
    • Jugador sale de detection_range             → WANDERING

    Cómo usarlo en un enemigo concreto
    ────────────────────────────────────
    1. Heredar de EnemyBrain en vez de LivingEntity.
    2. En update():
         state = self.brain_tick(dt, maze, player, player_bombs)
         if state == EnemyBrain.DEAD:      return
         if state == EnemyBrain.STUNNED:   return
         if state == EnemyBrain.ESCAPING:  return   # escape ya ejecutado
         if state == EnemyBrain.WAIT:      return   # wait ya ejecutado
         # state == CHASING o WANDERING: añadir lógica especial aquí
         self.move(dt, maze)
    3. Siempre terminar con:
         self.update_death(dt)
         self.animate(dt, moving=(self.direction != (0, 0)))

    Hooks opcionales (override en subclases)
    ─────────────────────────────────────────
    on_start_chase(player)      Llamado al entrar en CHASING la primera vez.
    on_start_wander()           Llamado al entrar en WANDERING.
    on_start_escape(bomb, cell) Llamado al detectar la bomba.
    on_escape_done()            Llamado al terminar el escape.
    ignore_bricks_while_chasing() → bool  Por defecto False; Ghost lo sobreescribe.
    """

    # Constantes de estado — usadas externamente para comparar
    DEAD      = 'dead'
    STUNNED   = 'stunned'
    ESCAPING  = 'escaping'
    WAIT      = 'wait'
    CHASING   = 'chasing'
    WANDERING = 'wandering'

    def __init__(self, pos, width, height, speed, animations, lives=1,
                 detection_range=5, initial_status='down', animation_speed=5):
        super().__init__(pos, width, height, speed, animations, lives,
                         detection_range, initial_status, animation_speed)

        # Estado actual de la máquina
        self._brain_state      = self.WANDERING
        self._prev_brain_state = None

        # Última posición libre de bombas — usada para desencierro
        self._last_safe_pos    = (pos[0], pos[1])

        # Caché de detección de bomba: evita recalcular A* cada frame
        # cuando hay muchas bombas en pantalla
        self._danger_cache          = (None, None)   # (bomb, escape_cell)
        self._danger_cache_timer    = 0.0
        self._danger_cache_duration = 0.15           # recalcular cada 0.15s

    # ── Hooks opcionales ──────────────────────────────────────────────────────

    def on_start_chase(self, player):
        """Llamado una vez al entrar en CHASING. Override opcional."""
        pass

    def on_start_wander(self):
        """Llamado una vez al entrar en WANDERING. Override opcional."""
        pass

    def on_start_escape(self, bomb, escape_cell):
        """Llamado una vez al detectar bomba peligrosa. Override opcional."""
        pass

    def on_escape_done(self):
        """Llamado cuando el escape termina (bomba explotó o llegó a celda segura)."""
        pass

    def ignore_bricks_while_chasing(self):
        """
        Retorna True si el A* debe ignorar bricks durante CHASING.
        Ghost lo sobreescribe para devolver self.ghost_mode.
        """
        return False

    def get_chase_target(self, player):
        """
        Retorna el target real de persecución.
        Por defecto es el jugador. Bear lo sobreescribe para usar sniff_target.
        """
        return player

    def bomb_detection_instant(self):
        """
        Retorna True si este enemigo detecta bombas instantáneamente.
        Por defecto False (usa reaction_time). Robot sobreescribe a True
        para evitar fuego amigo con sus propias bombas y las del jugador.
        """
        return False

    # ── Motor principal ───────────────────────────────────────────────────────

    def brain_tick(self, dt, maze, player, player_bombs=None):
        """
        Avanza la máquina de estados un frame y ejecuta la acción correspondiente.

        Debe llamarse AL INICIO del update() del enemigo, antes de cualquier
        lógica especial. Retorna el estado resultante para que el enemigo
        decida si necesita añadir comportamiento extra o simplemente retornar.

        Args:
            dt           : Delta time del frame.
            maze         : Instancia del laberinto actual.
            player       : Entidad objetivo (jugador). Puede ser None.
            player_bombs : Lista de bombas del jugador. None = sin amenaza.

        Returns:
            str: Una de las constantes DEAD / STUNNED / ESCAPING / WAIT /
                 CHASING / WANDERING.
        """
        # Descontar timers de post-escape incondicionalmente — si solo se
        # decrementan dentro de update_wait_state, un stun o muerte temporal
        # los deja atascados y el enemigo nunca vuelve a detectar bombas.
        if self._escape_cooldown > 0:
            self._escape_cooldown -= dt
        if self._in_wait_state:
            self._wait_timer -= dt
            if self._wait_timer <= 0:
                self._in_wait_state = False
                self._wait_timer    = 0.0
        # ── 1. DEAD ───────────────────────────────────────────────────────────
        if self.dead:
            self._set_state(self.DEAD)
            self.update_death(dt)
            self.animate(dt, moving=False)
            return self.DEAD

        # ── 2. STUNNED ────────────────────────────────────────────────────────
        if self.is_stunned:
            # Limpiar escape activo si la bomba ya desapareció durante el stun
            if self._escaping_bomb:
                bomb = self._bomb_being_escaped
                if bomb is None or getattr(bomb, 'remove', False) or getattr(bomb, 'exploded', False):
                    self._reset_escape_state()
            self._set_state(self.STUNNED)
            self.direction = (0, 0)
            self.update_death(dt)
            self.animate(dt, moving=False)
            return self.STUNNED

        # ── 3. ESCAPING — evasión de bomba del jugador ────────────────────────
        if self._escaping_bomb:
            bomb = self._bomb_being_escaped
            if bomb is None or getattr(bomb, 'remove', False) or getattr(bomb, 'exploded', False):
                self._finish_escape()
            else:
                still_escaping = self.smart_bomb_escape(bomb, self._escape_target_cell, maze, dt)
                if not still_escaping:
                    self._finish_escape()
                else:
                    # Aplicar movimiento físico — _move_toward_cell solo fija
                    # direction; sin move() el enemigo no se desplaza.
                    self.move(dt, maze)
                    self._set_state(self.ESCAPING)
                    self.update_death(dt)
                    self.animate(dt, moving=(self.direction != (0, 0)))
                    return self.ESCAPING

        # Buscar nueva amenaza solo si no estamos en WAIT ni cooldown
        if not self._in_wait_state and self._escape_cooldown <= 0:
            # Fusionar bombas del jugador con bombas extra (ej: Robot)
            # para que la detección sea unificada en un solo sistema.
            extra = getattr(self, '_extra_bombs', [])
            bombs_to_check = list(player_bombs or []) + [
                b for b in extra if b not in (player_bombs or [])
            ]
            bomb_threat, escape_cell = self.check_player_bomb_danger(
                bombs_to_check, maze, dt,
                instant=self.bomb_detection_instant()
            )
            if bomb_threat is not None and escape_cell is not None:
                escape_cell = self.on_start_escape(bomb_threat, escape_cell) or escape_cell
                self.smart_bomb_escape(bomb_threat, escape_cell, maze, dt)
                # Aplicar movimiento físico del primer frame de escape
                self.move(dt, maze)
                self._set_state(self.ESCAPING)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return self.ESCAPING

        # ── 4. WAIT ───────────────────────────────────────────────────────────
        if self._in_wait_state:
            in_wait = self.update_wait_state(dt)
            if in_wait:
                self._set_state(self.WAIT)
                self.update_death(dt)
                self.animate(dt, moving=(self.direction != (0, 0)))
                return self.WAIT
            # WAIT expiró: decidir qué estado sigue

        # ── 5. CHASING / WANDERING ────────────────────────────────────────────
        # La detección respeta los muros: se basa en la longitud del path A*,
        # no en la distancia Euclidiana. follow_player ya hace el cálculo del
        # path internamente, así que aquí solo decidimos el estado y lo dejamos
        # actuar — si el path es más largo que detection_range, follow_player
        # llamará random_walk por sí solo.
        if player is not None and not getattr(player, 'dead', False):
            new_state = self.CHASING   # follow_player decidirá si perseguir o no
        else:
            new_state = self.WANDERING

        # Disparar hooks de transición
        if new_state != self._brain_state:
            if new_state == self.CHASING:
                self.on_start_chase(player)
            elif new_state == self.WANDERING:
                self.on_start_wander()

        self._set_state(new_state)

        # Ejecutar movimiento según estado
        if new_state == self.CHASING:
            target = self.get_chase_target(player)
            self.follow_player(maze, target, dt,
                               ignore_bricks=self.ignore_bricks_while_chasing())
        else:
            self.random_walk(dt)

        return new_state

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _set_state(self, new_state):
        """Actualiza el estado registrando la transición."""
        self._prev_brain_state = self._brain_state
        self._brain_state = new_state

    def _finish_escape(self):
        """Cierra el escape activo y dispara on_escape_done."""
        self._reset_escape_state()   # → activa WAIT internamente
        self.on_escape_done()

    def _full_escape_reset(self):
        """
        Reset completo de TODOS los flags de escape, sin activar WAIT.
        Usar cuando el enemigo es aturdido, muere, o necesita un reset duro.
        """
        self._escaping_bomb         = False
        self._escape_target_cell    = None
        self._escape_committed      = False
        self._safe_from_bomb        = False
        self._bomb_being_escaped    = None
        self._bomb_perception_timer = 0.0
        self._bomb_perceived        = False
        self._danger_cache          = (None, None)
        self._danger_cache_timer    = 0.0
        self._in_wait_state         = False
        self._wait_timer            = 0.0
        self._escape_cooldown       = 0.0

    @property
    def brain_state(self):
        """Estado actual legible externamente (para debug)."""
        return self._brain_state

    def stun(self, duration):
        """
        Override: además de aturdir, hace reset completo de flags de escape.
        Un enemigo aturdido no puede escapar, y sus flags deben quedar limpios
        para que al recuperarse pueda detectar nuevas amenazas normalmente.
        """
        super().stun(duration)
        self._full_escape_reset()


# UTILIDADES

def load_animations_from_dict(animations_dict):
    """
    Carga animaciones desde un diccionario de configuración.
    
    Args:
        animations_dict: Dict {status: [filenames]}
    
    Returns:
        Dict {status: [surfaces]}
    
    Ejemplo:
        animations_config = {
            'down': ['front_stand.png', 'front_m01.png'],
            'up': ['back_stand.png', 'back_m01.png']
        }
        animations = load_animations_from_dict(animations_config)
    """
    loaded_animations = {}
    
    for status, filenames in animations_dict.items():
        loaded_animations[status] = [load_image(f) for f in filenames]
    
    return loaded_animations