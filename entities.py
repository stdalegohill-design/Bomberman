"""
ENTITIES.PY - Clases Base para Entidades
=========================================

Jerarquía de herencia:
    AnimatedEntity (base pygame.sprite.Sprite)
     MovableEntity
         PathfindingEntity
             LivingEntity

Estas clases eliminan código repetitivo y proveen funcionalidad común
para todos los personajes (jugadores y enemigos) del juego.

Clases:
--------

AnimatedEntity(pygame.sprite.Sprite):
    Clase base para cualquier entidad con animación.
    
    Hereda de: pygame.sprite.Sprite
    Heredada por: MovableEntity, Bomb
    
    Atributos principales:
    - animations: Dict de animaciones por estado
    - current_animation: Lista de frames actual
    - animation_frame: Frame actual de la animación
    - animation_speed: Velocidad de cambio de frames
    
    Métodos principales:
    - change_animation(): Cambia el estado de animación
    - animate(): Actualiza el frame actual

MovableEntity(AnimatedEntity):
    Añade física básica: movimiento, velocidad y colisiones.
    
    Hereda de: AnimatedEntity
    Heredada por: PathfindingEntity
    
    Atributos principales:
    - x, y: Posición en píxeles
    - width, height: Dimensiones
    - speed: Velocidad de movimiento
    - direction: Dirección actual (dx, dy)
    
    Métodos principales:
    - move(): Aplica movimiento con detección de colisiones
    - random_walk(): Movimiento aleatorio

PathfindingEntity(MovableEntity):
    Añade IA: pathfinding A*, detección de jugador, evasión de bombas.
    
    Hereda de: MovableEntity
    Heredada por: LivingEntity
    
    Atributos principales:
    - detection_range: Rango de detección del jugador
    - path: Camino A* calculado hacia objetivo
    - escaping_bomb: Estado de huida de bomba
    - in_wait_state: Estado de espera después de huir
    
    Métodos principales:
    - find_path(): Calcula ruta A* hacia objetivo
    - follow_player(): Persigue al jugador
    - check_player_bomb_danger(): Detecta bombas peligrosas
    - smart_bomb_escape(): Huye de bombas con anti-vibración
    - update_wait_state(): Maneja estado de espera post-huida

LivingEntity(PathfindingEntity):
    Añade sistema de vidas: daño, muerte, invencibilidad, stun.
    
    Hereda de: PathfindingEntity
    Heredada por: PlayerBomberman, Ghost, Snow, Bear, Robot, Water, Globe, Barrel
    
    Atributos principales:
    - lives: Vidas actuales
    - max_lives: Vidas máximas
    - dead: Estado de muerte
    - invincibility_timer: Temporizador de invencibilidad
    - is_stunned: Estado de aturdimiento por bomba
    
    Métodos principales:
    - take_damage(): Recibe daño y maneja invencibilidad
    - die(): Ejecuta muerte (animación y lógica)
    - stun(): Aturde temporalmente
    - is_stunned(): Verifica si está aturdido
    - update_death(): Actualiza animación de muerte

Uso típico:
-----------
    # Cárear un nuevo enemigo
    class NewEnemy(LivingEntity):
        def __init__(self, pos):
            animations = load_animations_from_dict({...})
            super().__init__(
                pos=pos,
                width=32, height=32,
                speed=80,
                animations=animations,
                lives=1,
                detection_range=5
            )
        
        def update(self, dt, maze, player):
            # Lógica específica del enemigo
            distance = math.hypot(player.x - self.x, player.y - self.y)
            if distance < self.detection_range * maze.cell_size:
                self.follow_player(maze, player, dt)
            self.move(dt, maze)
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
            
            # Alinear al grid si choca
            if self.direction[0] > 0:
                self.x = (next_x // maze.cell_size) * maze.cell_size
            elif self.direction[0] < 0:
                self.x = ((next_x // maze.cell_size) + 1) * maze.cell_size

            if self.direction[1] > 0:
                self.y = (next_y // maze.cell_size) * maze.cell_size
            elif self.direction[1] < 0:
                self.y = ((next_y // maze.cell_size) + 1) * maze.cell_size

            # NO reseteamos direction aquí: follow_player la áreasigna cada frame.
            # Si reseteamos, el enemigo queda quieto 1 frame entre cada celda
            # y en giros parece "trabado". Solo resetear en random_walk.
            self.rect.topleft = (self.x, self.y)
            self.pos = (self.x, self.y)
            return True  # Hubo colisión
        else:
            # Movimiento libre
            self._blocked_by_bomb = False  # Resetear flag
            self.x = next_x
            self.y = next_y
            self.rect.topleft = (self.x, self.y)
            self.pos = (self.x, self.y)
            return False
    
    def _check_bomb_collision(self, entity_rect):
        """
        Verifica si el enemigo colisionaría con bombas sólidas.
        
        NUEVO: Enemigos respetan bombas como obstáculos
        
        Args:
            entity_rect: Rectángulo del enemigo en próxima posición
        
        Returns:
            bool: True si hay colisión con bomba sólida
        """
        # Obtener lista de bombas si está disponible (asignada por game_level)
        all_bombs = getattr(self, '_all_bombs', [])
        
        for bomb in all_bombs:
            # Solo colisionar con bombas sólidas
            if not bomb.is_solid:
                continue
            
            # Ignorar bombas que ya explotaron
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
        self._wait_duration = 2.0
        self._escape_cooldown = 0.0
        self._escape_cooldown_duration = 1.5
        
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
    
    def _nearby_bomb_danger(self, all_bombs, safety_radius_cells=4):
        """
        Detecta si alguna bomba activa (de Robot o de jugador) supone
        peligro inminente para esta entidad.

        Usado por TODOS los enemigos (Ghost, Snow, Bear, Barrel, Robot)
        porque está en la clase padre PathfindingEntity.

        Args:
            all_bombs           : iterable de objetos Bomb
            safety_radius_cells : radio en celdas considerado peligroso

        Returns:
            (Bomb, (escape_row, escape_col))  si hay peligro
            (None, None)                       si está seguro
        """
        cs = CELL_SIZE
        my_col = int(self.x // cs)
        my_row = int(self.y // cs)

        for bomb in all_bombs:
            if getattr(bomb, 'remove', False):
                continue
            # Peligrosa si: ya explotó O le quedan < 1.8 s de mecha
            is_dangerous = (
                getattr(bomb, 'exploded', False) or
                (not getattr(bomb, 'exploded', False) and
                 getattr(bomb, 'timer', 999) < 1.8)
            )
            if not is_dangerous:
                continue

            dist = abs(bomb.x - self.x) + abs(bomb.y - self.y)
            if dist > safety_radius_cells * cs:
                continue

            bomb_col = int(bomb.x // cs)
            bomb_row = int(bomb.y // cs)
            maze = self._maze_ref

            # Candidatos: vecinos libres, ordenados de más lejos a más cerca de la bomba
            candidates = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                er, ec = my_row + dr, my_col + dc
                if maze is not None:
                    if not (0 < er < maze.rows - 1 and 0 < ec < maze.cols - 1):
                        continue
                    if maze.grid[er][ec] in ('ironbrick', 'brick'):
                        continue
                dist_from_bomb = abs(er - bomb_row) + abs(ec - bomb_col)
                candidates.append((dist_from_bomb, (er, ec)))

            if candidates:
                candidates.sort(reverse=True)
                return bomb, candidates[0][1]

        return None, None
    
    def smart_bomb_escape(self, bomb, escape_cell, maze, dt):
        """
        Escape inteligente de bombas - versión anti-vibración.
        
        Lógica:
        1. Primera vez: Calcular celda de escape y comprometerse
        2. Moverse hacia esa celda (sin recalcular)
        3. Al llegar: Quedarse quieto hasta que explote
        4. Si la bomba explota: Resetear estado
        
        Args:
            bomb: Bomba peligrosa
            escape_cell: Celda de escape calculada (row, col)
            maze: Mapa
            dt: Delta time
        
        Returns:
            bool: True si está manejando el escape (no hacer nada más)
        """
        cs = maze.cell_size
        my_col = int(self.x // cs)
        my_row = int(self.y // cs)
        
        # Primera vez escapando de esta bomba
        if not self._escaping_bomb:
            self._escaping_bomb = True
            self._escape_target_cell = escape_cell
            self._escape_committed = True
            self._safe_from_bomb = False
            self._bomb_being_escaped = bomb
        
        # Verificar si la bomba ya explotó o desapareció
        if getattr(bomb, 'remove', True) or getattr(bomb, 'exploded', False):
            self._reset_escape_state()
            return False
        
        # Si ya llegamos a la celda de escape
        if (my_row, my_col) == self._escape_target_cell:
            # Bug #2 fix: hacer snap exacto al centro de celda para evitar
            # micro-oscilaciones provocadas por decimales residuales de posicion.
            target_row, target_col = self._escape_target_cell
            snap_x = target_col * cs
            snap_y = target_row * cs
            if abs(self.x - snap_x) < self.speed * 0.05:
                self.x = snap_x
            if abs(self.y - snap_y) < self.speed * 0.05:
                self.y = snap_y
            self.rect.topleft = (self.x, self.y)

            if self._is_safe_from_explosion(bomb, maze):
                self._safe_from_bomb = True
                self.direction = (0, 0)
                return True

        # Si ya estamos a salvo, solo esperar
        if self._safe_from_bomb:
            self.direction = (0, 0)
            return True
        
        # Moverse hacia la celda de escape (sin recalcular)
        self._move_toward_cell(self._escape_target_cell, maze, dt)
        return True
    
    def _is_safe_from_explosion(self, bomb, maze):
        """
        Verifica si la posición actual está a salvo de la explosión.
        
        Args:
            bomb: Bomba a verificar
            maze: Mapa
        
        Returns:
            bool: True si está fuera del rango de explosión
        """
        cs = maze.cell_size
        my_col = int(self.x // cs)
        my_row = int(self.y // cs)
        
        bomb_col = int(bomb.x // cs)
        bomb_row = int(bomb.y // cs)
        
        bomb_range = getattr(bomb, 'explosion_range', 2)
        
        # Misma fila/columna = peligro si está en rango
        if my_row == bomb_row:
            dist = abs(my_col - bomb_col)
            if dist <= bomb_range:
                # Verificar si hay muro entre nosotros
                if self._wall_blocks_explosion(my_row, my_col, bomb_row, bomb_col, maze):
                    return True
                return False
        
        if my_col == bomb_col:
            dist = abs(my_row - bomb_row)
            if dist <= bomb_range:
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
        """Resetea el estado de escape y entra en WAIT."""
        self._escaping_bomb = False
        self._escape_target_cell = None
        self._escape_committed = False
        self._safe_from_bomb = False
        self._bomb_being_escaped = None
        
        self._in_wait_state = True
        self._wait_timer = self._wait_duration
        self._escape_cooldown = self._escape_cooldown_duration

    def update_wait_state(self, dt):
        """Actualiza el estado WAIT (espera después de escapar)."""
        if self._escape_cooldown > 0:
            self._escape_cooldown -= dt
        
        if not self._in_wait_state:
            return False
        
        self._wait_timer -= dt
        
        if self._wait_timer > 0:
            import random
            if random.random() < 0.2:
                self.random_walk(dt)
            else:
                self.direction = (0, 0)
            return True
        
        self._in_wait_state = False
        self._wait_timer = 0.0
        return False

    def _move_toward_cell(self, target_cell, maze, dt):
        """
        Mueve la entidad un paso hacia la celda objetivo (row, col).
        Lógica extraída de follow_player para reutilizar en evasión de bombas.
        """
        cs = maze.cell_size
        my_cell = (int(self.y // cs), int(self.x // cs))
        next_row, next_col = target_cell

        target_cx = next_col * cs + cs // 2
        target_cy = next_row * cs + cs // 2

        dx = target_cx - (self.x + self.width  // 2)
        dy = target_cy - (self.y + self.height // 2)

        if abs(dx) >= abs(dy):
            self.direction = (1 if dx > 0 else -1, 0)
            self.change_animation('right' if dx > 0 else 'left')
            row_center_y = my_cell[0] * cs + cs // 2 - self.height // 2
            diff_y = row_center_y - self.y
            if abs(diff_y) > 0.5:
                step = min(abs(diff_y), self.speed * dt * 0.5)
                self.y += step if diff_y > 0 else -step
        else:
            self.direction = (0, 1 if dy > 0 else -1)
            self.change_animation('down' if dy > 0 else 'up')
            col_center_x = my_cell[1] * cs + cs // 2 - self.width // 2
            diff_x = col_center_x - self.x
            if abs(diff_x) > 0.5:
                step = min(abs(diff_x), self.speed * dt * 0.5)
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
        my_cell = (int(self.y // cs), int(self.x // cs))

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
        
        # Recalcular solo si:
        # - No hay caché
        # - El objetivo cambió
        # - Ha pasado suficiente tiempo
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

        if path:
            self._move_toward_cell(path[0], maze, dt)
        else:
            self.random_walk(dt)


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
        self._bomb_áreaction_time    = 1.5   # override en __init__ de cada subclase

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
    
    def check_player_bomb_danger(self, player_bombs, maze, dt):
        """
        Detecta si hay una bomba del jugador peligrosa cerca, con retraso de percepcion.

        - Acumula _bomb_perception_timer mientras haya bomba en rango.
        - Al superar _bomb_áreaction_time dispara el escape y muestra '!'.
        - Si la bomba desaparece antes de ser percibida, resetea el timer.

        Returns:
            (Bomb, escape_cell) si debe escapar ahora, (None, None) si no.
        """
        
        if self._in_wait_state or self._escape_cooldown > 0:
            self._bomb_perception_timer = 0.0
            self._bomb_perceived = False
            return None, None
        
        if self.dead or self.is_stunned:
            self._bomb_perception_timer = 0.0
            self._bomb_perceived        = False
            return None, None

        # Buscar bomba peligrosa cercana (usa el metodo heredado de PathfindingEntity)
        bomb_tháreat, escape_cell = self._nearby_bomb_danger(
            player_bombs, safety_radius_cells=4
        )

        if bomb_tháreat is None:
            # No hay bomba cercana: resetear acumulador
            self._bomb_perception_timer = 0.0
            self._bomb_perceived        = False
            return None, None

        if self._bomb_perceived:
            # Ya la percibio: seguir escapando (no resetear)
            return bomb_tháreat, escape_cell

        # Acumular tiempo de percepcion
        self._bomb_perception_timer += dt
        if self._bomb_perception_timer >= self._bomb_áreaction_time:
            # PERCIBIDA: activar escape y signo '!'
            self._bomb_perceived    = True
            self._exclamation_timer = 1.2   # segundos que dura el '!'
            return bomb_tháreat, escape_cell

        # Aun no la percibe
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