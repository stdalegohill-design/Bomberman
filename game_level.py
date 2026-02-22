"""
GAME_LEVEL.PY - Gestor del Nivel de Juego
==========================================

Coordina todos los elementos y sistemas de un nivel en curso:
- Generacin y renderizado del mapa
- Gestin de jugadores (1-4)
- Sistema de cmara (simple o split-screen)
- Spawning y actualizacin de enemigos
- Sistema de bombas y explosiones
- Power-ups y efectos especiales
- Deteccin de victoria y derrota
- Integracin de audio

Acta como el "cerebro" del nivel, orquestando la interaccin entre
todos los subsistemas del juego.

Jerarqua de clases:
    Sin herencia - Clase independiente

Clase:
------

LevelManager:
    Gestor principal del nivel de juego.
    
    No hereda de ninguna clase
    Usada por: PlayingState para ejecutar el gameplay
    
    Responsabilidades principales:
    
    1. Inicializacin del nivel:
       - Genera mapa con Maze
       - Crea jugadores en spawns
       - Spawna enemigos segn dificultad
       - Configura cmara segn nmero de jugadores
       - Inicializa audio del nivel
    
    2. Gestin de jugadores:
       - Actualiza posicin y estado
       - Procesa input de controles
       - Maneja colisiones
       - Aplica efectos de tiles (nieve, charcos)
       - Gestiona bombas de cada jugador
    
    3. Gestin de enemigos:
       - Spawning inicial por tipo
       - Actualizacin de comportamiento IA
       - Deteccin de amenazas (bombas)
       - Sistema de escape inteligente
       - Spawning especial (Barrel  enemigo aleatorio)
    
    4. Sistema de bombas:
       - Actualizacin de todas las bombas activas
       - Deteccin de explosiones
       - Aplicacin de dao a jugadores y enemigos
       - Destruccin de bricks con drop de power-ups
       - Explosiones en cadena
    
    5. Sistema de power-ups:
       - Spawning al destruir bricks
       - Deteccin de recoleccin
       - Aplicacin de efectos
       - Gestin de tiles especiales (nieve, agua)
    
    6. Sistema de cmara:
       - Cmara simple (1 jugador)
       - Split-screen diagonal (2 jugadores)
       - Seguimiento de jugadores
       - Renderizado con viewport correcto
    
    7. Victoria y derrota:
       - Verifica muerte de todos los jugadores (Game Over)
       - Verifica eliminacin de todos los enemigos (puerta abierta)
       - Verifica entrada a puerta (Victoria)
    
    Atributos principales:
    ----------------------
    
    Configuracin:
    - game: Referencia al Game principal
    - num_players: Cantidad de jugadores (1-4)
    - difficulty: Nivel de dificultad (EASY/NORMAL/HARD/EXPERT)
    - audio: AudioManager para másica y SFX
    
    Mapa y cmara:
    - maze: Instancia de Maze con el laberinto
    - camera: Camera o SplitCamera segn jugadores
    
    Entidades:
    - players: Lista de PlayerBomberman activos
    - enemies: Lista de enemigos vivos
    - powerups: Lista de power-ups en el mapa
    - snow_tiles: Tiles de nieve activas
    - water_puddles: Charcos de agua activos
    
    Estado del nivel:
    - level_number: Nmero del nivel actual
    - gameover: Si todos los jugadores murieron
    - victory: Si algn jugador lleg a la puerta
    - door_opened: Si la puerta est abierta
    
    Mtodos principales:
    --------------------
    
    Inicializacin:
    - __init__(): Crea el nivel con jugadores y dificultad
    - load_level(): Genera mapa, spawns y configura cmara
    
    Loop principal:
    - handle_events(): Procesa eventos (actualmente delegado a estados)
    - update(): Actualiza todos los sistemas del nivel
    - draw(): Renderiza todo (mapa, entidades, UI)
    
    Actualizacin por sistema:
    - _update_players(): Actualiza jugadores y sus bombas
    - _update_enemies(): Actualiza enemigos con IA
    - _update_bombs(): Actualiza todas las bombas activas
    - _update_powerups(): Actualiza power-ups y efectos
    
    Sistemas auxiliares:
    - _spawn_enemies(): Spawning inicial de enemigos
    - _spawn_enemy_type(): Crea enemigo especfico en posicin
    - _spawn_from_barrel(): Spawning de enemigo al matar Barrel
    - _check_enemy_bomb_threats(): Sistema de evasin de bombas
    - _check_bomb_hits(): Aplica dao de explosiones
    
    Condiciones de fin:
    - check_gameover(): Verifica si todos murieron
    - check_victory(): Verifica si ganaron
    
    Renderizado:
    - draw_grid_on_viewport(): Dibuja mapa en viewport especfico
    - scaled_rect(): Convierte rect de mundo a pantalla
    
    Limpieza:
    - cleanup(): Libera recursos al salir del nivel
    
    Sistema de spawning de enemigos:
    ---------------------------------
    Configurado por dificultad y nivel:
    
    EASY: Menos enemigos, más lentos
    NORMAL: Cantidad y velocidad base
    HARD: Ms enemigos, más rpidos
    EXPERT: Muchos enemigos, muy rpidos
    
    Tipos de enemigos por nivel:
    - Nivel 1: Ghost, Snow
    - Nivel 2: Ghost, Snow, Bear
    - Nivel 3: Ghost, Snow, Bear, Robot
    - Nivel 4+: Todos los tipos
    
    Spawning seguro:
    - Verifica que celda est vaca
    - No spawna cerca de jugadores
    - Robot: Verifica espacio para sus bombas
    - Barrel: Spawning normal con habilidad especial
    
    Sistema de explosiones:
    -----------------------
    1. Bomba explota (timer = 0)
    2. Calcula celdas afectadas en cruz
    3. Destruye bricks  spawna power-ups (40% chance)
    4. Aplica dao a jugadores en rango
    5. Aplica dao a enemigos en rango
    6. Detona bombas en cadena
    
    Sistema de cmara split:
    ------------------------
    En 2 jugadores:
    - Diagonal dinmica segn posicin relativa
    - Cada jugador ve su zona de la pantalla
    - Renderizado optimizado (solo dibuja celdas visibles)
    - Lnea divisoria visual
    
    Uso tpico:
    -----------
        # Crear nivel
        level = LevelManager(
            game=game,
            num_players=2,
            difficulty='NORMAL',
            audio=audio_manager
        )
        level.load_level(level_number=1)
        
        # Loop principal
        while playing:
            level.handle_events(events)
            level.update(dt)
            level.draw()
            
            # Verificar fin
            if level.gameover:
                # Ir a GameOverState
            elif level.victory:
                # Ir a VictoryState
        
        # Limpiar
        level.cleanup()
    
    Integracin con audio:
    ----------------------
    - Msica de nivel segn nmero
    - SFX de bomba (colocar, explosión)
    - SFX de power-up (recoger)
    - SFX de puerta (abrir)
    - SFX de muerte (jugador, enemigo)
    
    Performance:
    ------------
    - Renderizado optimizado por viewport
    - Solo actualiza entidades visibles (futuro)
    - Pooling de explosiones (futuro)
    - Lmite de bombas activas por jugador
"""


import pygame
import random
from settings import (
    CELL_SIZE, MAP_COLS, MAP_ROWS, WINDOW_WIDTH, WINDOW_HEIGHT,
    BombermanConfig, LevelConfig, DebugConfig, Colors, WaterConfig,
    DifficultyConfig, DynamicLevelGenerator, PowerUpConfig
)
from utils import draw_text, draw_health_bar, pixel_to_grid
from map import Camera, Maze, MultiCamera, SplitCamera
from player_bomberman import PlayerBomberman
from enemies import Ghost, Snow, Bear, Barrel, Robot, Water, Globe
from powerups import PowerUp, SnowTile, try_drop_powerup, Key


class LevelManager:
    """Gestiona un nivel completo del juego."""
    
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.font_small = game.font_small
        
        # Sistema de dificultad
        difficulty_name = getattr(game, 'difficulty', 'NORMAL')
        self.difficulty_config = DifficultyConfig.get_config(difficulty_name)
        self.difficulty_name = difficulty_name
        
        print(f"\n{'='*60}")
        print(f"DIFICULTAD: {difficulty_name}")
        print(f"   Multiplicador enemigos: {self.difficulty_config['enemy_count_multiplier']:.0%}")
        print(f"   Vidas jugador: {self.difficulty_config['player_lives']}")
        print(f"   Velocidad enemigos: {self.difficulty_config['enemy_speed_multiplier']:.0%}")
        print(f"{'='*60}\n")
        
        # Componentes del nivel
        self.maze    = None
        self.camera  = None

        # Jugadores (lista; se mantiene self.bomberman como alias a players[0])
        self.players = []

        # Entidades
        self.enemies    = []
        self.bombs      = []
        self.powerups   = []
        self.snow_tiles = []
        self.puddle_tiles = []
        self.enemy_powerups = []

        # Estado del nivel
        self.current_level  = 1
        self.score          = 0
        self.enemies_killed = 0
        self.num_players    = 1
        self.level_complete = False   # True cuando jugador toca puerta abierta

        # Sistema llave/puerta
        self.keys                  = []
        self._key_enemies_assigned = False
        
        # Audio (referencia al manager global)
        self.audio = game.audio

        # Debug
        self.show_debug = DebugConfig.SHOW_FPS
        self.show_grid = DebugConfig.SHOW_GRID
        self.show_hitbox = DebugConfig.SHOW_HITBOXES
        self.show_pathfinding = DebugConfig.SHOW_PATHFINDING
    
    # INICIALIZACIÓN
    
    def load_level(self, level_number):
        """
        Carga un nivel específico.
        
        Args:
            level_number: Número del nivel (1, 2, 3...)
        """
        self.current_level = level_number
        print(f"\n{'='*60}")
        print(f"CARGANDO NIVEL {level_number}")
        print(f"{'='*60}")
        
        # Posición de spawn
        player_start_x = CELL_SIZE + 4  # Alineado al centro de celda
        player_start_y = CELL_SIZE * 2
        
        # Crear mapa con densidad según dificultad
        brick_density = DynamicLevelGenerator.get_level_brick_density(
            level_number,
            self.difficulty_config
        )
        self.maze = Maze(MAP_ROWS, MAP_COLS, CELL_SIZE, (player_start_x, player_start_y))
        self.maze.generate(num_players=self.num_players, brick_density=brick_density)
        
        # Crear cámara según número de jugadores
        if self.num_players >= 2:
            self.camera = SplitCamera(WINDOW_WIDTH, WINDOW_HEIGHT,
                                      self.maze.width, self.maze.height)
        else:
            self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT,
                                 self.maze.width, self.maze.height)
        
        # Crear jugadores usando las celdas de spawn del mapa
        spawn_cells = self.maze._spawn_cells(self.num_players)
        self.players = []
        for pid in range(1, self.num_players + 1):
            sr, sc = spawn_cells[pid - 1]
            px = sc * CELL_SIZE
            py = sr * CELL_SIZE
            self.maze.grid[sr][sc] = 'empty'
            player = PlayerBomberman((px, py), player_id=pid)
            player.audio = self.audio
            player.set_font(self.font_small)
            self.players.append(player)
            print(f"   {player.label}: spawn en col={sc}, row={sr}")

        # Alias para retrocompatibilidad
        self.bomberman = self.players[0]
        
        # Aplicar configuración de dificultad a jugadores
        player_lives = self.difficulty_config['player_lives']
        speed_bonus = self.difficulty_config['player_speed_bonus']
        bomb_bonus = self.difficulty_config.get('bomb_range_bonus', 0)
        
        for player in self.players:
            player.lives = player_lives
            player.max_lives = player_lives
            # Usar BombermanConfig.BASE_SPEED como referencia base
            # (PlayerBomberman no expone base_speed como atributo)
            base = getattr(player, 'base_speed',
                           getattr(player, '_base_speed',
                                   BombermanConfig.BASE_SPEED))
            player.speed = int(base * speed_bonus)

            if bomb_bonus > 0:
                player.bomb_range = getattr(player, 'bomb_range', 2) + bomb_bonus
        
        print(f"Jugadores: {self.num_players} con {player_lives} vidas cada uno")
        if speed_bonus != 1.0:
            print(f"   Velocidad: {int(speed_bonus * 100)}%")
        if bomb_bonus > 0:
            print(f"   Bonus rango: +{bomb_bonus}")
        
        # Limpiar entidades previas
        self.enemies.clear()
        self.bombs.clear()
        self.powerups.clear()
        self.snow_tiles.clear()
        self.puddle_tiles.clear()
        self.enemy_powerups.clear()
        self.keys.clear()
        self._key_enemies_assigned = False
        self.level_complete        = False
        for p in self.players:
            p.has_key = False
        
        # Generar enemigos según el nivel y dificultad (sistema híbrido)
        self._spawn_enemies(level_number)
        
        # Ajustar drop chance de powerups
        PowerUpConfig.DROP_CHANCE = self.difficulty_config['powerup_drop_chance']
        
        print(f"Nivel {level_number} cargado")
        # Música: breve jingle de inicio  luego loop del nivel
        self.game.audio.play_music('start', loops=0)
        # La pista del nivel empieza después del start; en un motor completo
        # se haría con un evento MUSIC_END, aquí la activamos directamente.
        self.game.audio.play_music('level_1')
        print(f"   Enemigos: {len(self.enemies)}")
        print(f"   Mapa: {MAP_COLS}x{MAP_ROWS}")
        print(f"{'='*60}\n")
    
    def _spawn_enemies(self, level_number):
        """
        Genera enemigos usando LevelConfig como base + multiplicador de dificultad.
        
        Sistema híbrido:
        - Base: LevelConfig.ENEMIES_PER_LEVEL (valores para NORMAL)
        - Escala: difficulty_config['enemy_multiplier']
        - Velocidad: difficulty_config['enemy_speed_multiplier']
        
        Args:
            level_number: Número del nivel (1-5+)
        """
        # Obtener configuración base del nivel
        base_config = LevelConfig.ENEMIES_PER_LEVEL.get(
            level_number,
            LevelConfig.ENEMIES_PER_LEVEL[5]  # Nivel 5 como máximo
        )
        
        # Obtener multiplicadores de dificultad
        multiplier = self.difficulty_config['enemy_count_multiplier']
        speed_multiplier = self.difficulty_config['enemy_speed_multiplier']
        
        print(f"\nSpawning enemigos - Nivel {level_number} ({self.difficulty_name.upper()})")
        print(f"   Multiplicador cantidad: x{multiplier}")
        print(f"   Multiplicador velocidad: x{speed_multiplier}")
        
        # Generar enemigos escalados
        for enemy_type, base_count in base_config.items():
            if base_count == 0:
                continue
            
            # Escalar cantidad con dificultad (mínimo 1 si base > 0)
            adjusted_count = max(1, int(base_count * multiplier))
            
            # Spawnar enemigos con velocidad ajustada
            spawned = self._spawn_enemy_type_with_speed(
                enemy_type, 
                adjusted_count,
                speed_multiplier
            )
        
        # Resumen
        print(f"\n   Enemigos generados:")
        for enemy_type in ['Ghost', 'Snow', 'Bear', 'Barrel', 'Robot', 'Water', 'Globe']:
            count = sum(1 for e in self.enemies if e.enemy_type == enemy_type)
            if count > 0:
                print(f"   {enemy_type}: {count}")
        print(f"   TOTAL: {len(self.enemies)} enemigos\n")
    
    def _spawn_enemy_type(self, enemy_type, count):
        """
        Genera enemigos de un tipo específico (sin ajuste de velocidad).
        Wrapper para compatibilidad con código viejo.
        
        Args:
            enemy_type: 'ghost', 'snow', 'bear', etc.
            count: Cantidad a generar
        """
        self._spawn_enemy_type_with_speed(enemy_type, count, speed_multiplier=1.0)
    
    def _spawn_enemy_type_with_speed(self, enemy_type, count, speed_multiplier=1.0):
        """
        Genera enemigos de un tipo especifico con ajuste de velocidad.

        Correcciones aplicadas:
        - Bug #5: verificacion estricta de celda 'empty' (nunca en brick/ironbrick).
        - Bug #4: Robot requiere zona segura de 3 celdas sin brick ni aliados,
          para poder escapar de sus propias bombas sin matarlos.

        Args:
            enemy_type      : 'ghost', 'snow', 'bear', etc.
            count           : Cantidad a generar
            speed_multiplier: Multiplicador de velocidad (de dificultad)

        Returns:
            int: Cantidad realmente spawneada
        """
        is_robot = enemy_type.lower() == 'robot'
        spawned  = 0

        for _ in range(count):
            attempts = 0
            while attempts < 100:
                col = random.randint(10, MAP_COLS - 2)
                row = random.randint(2, MAP_ROWS - 2)
                x   = col * CELL_SIZE
                y   = row * CELL_SIZE

                # Bug #5: la celda DEBE ser 'empty', nunca brick ni ironbrick
                if self.maze.grid[row][col] != 'empty':
                    attempts += 1
                    continue

                # Verificar distancia minima a jugadores (al menos 6 celdas)
                too_close = False
                for player in self.players:
                    dist = abs(x - player.x) + abs(y - player.y)
                    if dist < 6 * CELL_SIZE:
                        too_close = True
                        break
                if too_close:
                    attempts += 1
                    continue

                # Bug #4: Robot necesita zona de escape libre de brick en 3 celdas
                if is_robot and not self._robot_spawn_is_safe(row, col):
                    attempts += 1
                    continue

                # Crear enemigo
                enemy = None
                if enemy_type.lower() == 'ghost':
                    enemy = Ghost((x, y))
                elif enemy_type.lower() == 'snow':
                    enemy = Snow((x, y))
                elif enemy_type.lower() == 'bear':
                    enemy = Bear((x, y))
                elif enemy_type.lower() == 'barrel':
                    enemy = Barrel((x, y))
                elif enemy_type.lower() == 'robot':
                    enemy = Robot((x, y))
                elif enemy_type.lower() == 'water':
                    enemy = Water((x, y))
                elif enemy_type.lower() == 'globe':
                    enemy = Globe((x, y))

                if enemy:
                    if speed_multiplier != 1.0:
                        enemy.speed = int(enemy.speed * speed_multiplier)
                    self.enemies.append(enemy)
                    spawned += 1
                    break

                attempts += 1

        return spawned

    def _robot_spawn_is_safe(self, row, col):
        """
        Verifica que la celda de spawn de Robot tenga al menos 3 celdas
        despejadas en una direccion cardinal (ruta de escape de bomba).

        Un Robot que pone una bomba de rango 2 necesita al menos 3 celdas
        libres en alguna direccion para poder alejarse sin danar aliados
        ni matarse a si mismo.

        Returns:
            bool: True si la zona es apta para Robot
        """
        safe_radius = 3

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            free_cells = 0
            for step in range(1, safe_radius + 1):
                nr, nc = row + dr * step, col + dc * step
                if not (0 < nr < self.maze.rows - 1 and 0 < nc < self.maze.cols - 1):
                    break
                if self.maze.grid[nr][nc] == 'empty':
                    free_cells += 1
                else:
                    break  # Muro bloquea la ruta
            if free_cells >= safe_radius:
                return True

        return False
    
    def _spawn_from_barrel(self, barrel):
        """
        Crea los enemigos que estaban escondidos en el barril.
        Aparecen en la misma celda del barril y salen aturdidos.

        Args:
            barrel: Instancia de Barrel con pending_spawn relleno
        """
        from settings import BarrelConfig

        # Posición en grid del barril
        barrel_col = int(barrel.x // CELL_SIZE)
        barrel_row = int(barrel.y // CELL_SIZE)

        for spawn_type in barrel.pending_spawn:
            # Buscar celda vacía cercana (la del barril o las adyacentes)
            candidates = [
                (barrel_row, barrel_col),
                (barrel_row - 1, barrel_col),
                (barrel_row + 1, barrel_col),
                (barrel_row, barrel_col - 1),
                (barrel_row, barrel_col + 1),
            ]

            spawn_pos = None
            for r, c in candidates:
                if (0 <= r < self.maze.rows and
                        0 <= c < self.maze.cols and
                        self.maze.grid[r][c] == 'empty'):
                    spawn_pos = (c * CELL_SIZE, r * CELL_SIZE)
                    break

            if spawn_pos is None:
                continue  # No hay espacio, no spawnear

            # Crear el enemigo del tipo correcto
            if spawn_type == 'ghost':
                new_enemy = Ghost(spawn_pos)
            elif spawn_type == 'snow':
                new_enemy = Snow(spawn_pos)
            elif spawn_type == 'bear':
                new_enemy = Bear(spawn_pos)
            elif spawn_type == 'water':
                new_enemy = Water(spawn_pos)
            elif spawn_type == 'Globe':
                new_enemy = Globe(spawn_pos)
            else:
                continue

            # Aplicar aturdimiento E invencibilidad.
            # La invencibilidad es necesaria porque la explosión que
            # destruyó el barril sigue activa los frames siguientes:
            # sin ella, el enemigo recién creado muere al instante.
            # Usamos el mismo tiempo que el stun para que coincidan.
            new_enemy.stun(BarrelConfig.STUN_DURATION)
            new_enemy.invincibility_timer = BarrelConfig.STUN_DURATION

            self.enemies.append(new_enemy)

    # ENEMIGOS Y BOMBAS DEL ROBOT
    
    def _check_enemy_bomb_threats(self, robot_bombs, dt):
        """
        Sistema inteligente: Enemigos escapan de bombas sin vibrar.
        
        Mejoras:
        - Escape comprometido (no recalcular)
        - Quedarse quieto al llegar a lugar seguro
        - Usar habilidades especiales por tipo de enemigo
        
        Args:
            robot_bombs: Lista de bombas activas de todos los Robots
            dt: Delta time
        """
        if not robot_bombs:
            return
        
        for enemy in self.enemies:
            if enemy.enemy_type == 'Robot' or enemy.dead:
                continue
            
            # Si ya está escapando, continuar con el plan
            if enemy._escaping_bomb:
                bomb = enemy._bomb_being_escaped
                
                # Verificar que la bomba sigue existiendo
                if bomb in robot_bombs and not getattr(bomb, 'remove', True):
                    # Usar escape inteligente
                    is_escaping = enemy.smart_bomb_escape(
                        bomb, 
                        enemy._escape_target_cell, 
                        self.maze, 
                        dt
                    )
                    
                    if is_escaping:
                        # Marcar para que no haga nada más este frame
                        enemy._skip_normal_update = True
                        continue
                else:
                    # Bomba explotó o desapareció
                    enemy._reset_escape_state()
            
            # No está escapando: Detectar nuevas amenazas
            bomb_threat, escape_cell = enemy._nearby_bomb_danger(
                robot_bombs, 
                safety_radius_cells=4  # CORREGIDO: Nombre correcto
            )
            
            if bomb_threat is not None and escape_cell is not None:
                # ===== LÓGICA ESPECIAL POR TIPO DE ENEMIGO =====
                
                # Ghost: Puede atravesar muros con habilidad
                if enemy.enemy_type == 'Ghost':
                    escape_cell = self._ghost_smart_escape(enemy, bomb_threat, escape_cell)
                
                # Globe: Puede volar sobre obstáculos
                elif enemy.enemy_type == 'Globe':
                    escape_cell = self._globe_smart_escape(enemy, bomb_threat, escape_cell)
                
                # Bear: Si está olfateando, esperar
                elif enemy.enemy_type == 'Bear':
                    if getattr(enemy, 'is_sniffing', False):
                        # Quedarse quieto hasta que termine de olfatear
                        enemy.direction = (0, 0)
                        continue
                
                # Iniciar escape inteligente
                enemy.smart_bomb_escape(bomb_threat, escape_cell, self.maze, dt)
                enemy._skip_normal_update = True
    
    def _ghost_smart_escape(self, ghost, bomb, default_escape_cell):
        """
        Ghost puede usar modo fantasma para atravesar muros.
        
        Returns:
            (row, col): Mejor celda de escape usando habilidad
        """
        # Si modo fantasma está disponible
        if ghost.ghost_cooldown_timer <= 0:
            # Activar modo fantasma
            ghost.activate_ghost_mode()
            
            # Buscar celda al otro lado del muro más cercano
            cs = self.maze.cell_size
            my_col = int(ghost.x // cs)
            my_row = int(ghost.y // cs)
            
            # Intentar ir al lado opuesto de la bomba atravesando muro
            bomb_col = int(bomb.x // cs)
            bomb_row = int(bomb.y // cs)
            
            # Dirección opuesta a la bomba
            if my_col < bomb_col:
                target_col = my_col - 3  # Ir más a la izquierda
            else:
                target_col = my_col + 3  # Ir más a la derecha
            
            if my_row < bomb_row:
                target_row = my_row - 3
            else:
                target_row = my_row + 3
            
            # Verificar límites
            target_col = max(1, min(target_col, self.maze.cols - 2))
            target_row = max(1, min(target_row, self.maze.rows - 2))
            
            return (target_row, target_col)
        
        # Modo fantasma no disponible, escape normal
        return default_escape_cell
    
    def _globe_smart_escape(self, globe, bomb, default_escape_cell):
        """
        Globe puede volar sobre obstáculos.
        
        Returns:
            (row, col): Mejor celda de escape usando vuelo
        """
        # Si puede volar
        if globe.fly_timer <= 0 and not globe.is_flying:
            # Activar vuelo
            globe.is_flying = True
            globe.fly_duration_timer = 0.0
            globe.change_animation('flying')
            
            # Calcular celda ideal (puede ignorar muros)
            cs = self.maze.cell_size
            my_col = int(globe.x // cs)
            my_row = int(globe.y // cs)
            
            bomb_col = int(bomb.x // cs)
            bomb_row = int(bomb.y // cs)
            
            # Ir lejos de la bomba en diagonal
            if my_col < bomb_col:
                target_col = my_col - 4
            else:
                target_col = my_col + 4
            
            if my_row < bomb_row:
                target_row = my_row - 4
            else:
                target_row = my_row + 4
            
            target_col = max(1, min(target_col, self.maze.cols - 2))
            target_row = max(1, min(target_row, self.maze.rows - 2))
            
            return (target_row, target_col)
        
        return default_escape_cell
    
    # EVENTOS
    
    def handle_events(self, events):
        """Maneja eventos específicos del nivel."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Toggle debug
                if event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    print(f"Debug: {'ON' if self.show_debug else 'OFF'}")
                
                if event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                    print(f"Grid: {'ON' if self.show_grid else 'OFF'}")
                
                if event.key == pygame.K_b:
                    self.show_hitbox = not self.show_hitbox
                    print(f"Hitbox: {'ON' if self.show_hitbox else 'OFF'}")
                
                if event.key == pygame.K_p:
                    self.show_pathfinding = not self.show_pathfinding
                    print(f"Pathfinding: {'ON' if self.show_pathfinding else 'OFF'}")
                
                # Simular daño (debug)
                if event.key == pygame.K_h:
                    if not self.bomberman.dead:
                        self.bomberman.hit = True
    
    # UPDATE
    
    def update(self, dt):
        """Actualiza toda la lógica del nivel."""
        # Si TODOS los jugadores terminaron  no actualizar
        if all(p.finish for p in self.players):
            return

        # NUEVO: Recopilar todas las bombas ANTES de actualizar jugadores
        all_bombs = []
        for player in self.players:
            all_bombs.extend(player.bombs)
        for enemy in self.enemies:
            if enemy.enemy_type == 'Robot' and hasattr(enemy, 'bombs'):
                all_bombs.extend(enemy.bombs)
        
        # Asignar other_bombs a cada jugador temporalmente
        # NOTA: Incluye TODAS las bombas; cada bomba individual excluye solo a sí misma
        for player in self.players:
            player._other_bombs = all_bombs  # CORREGIDO: Incluye todas (incluso propias)
            # NUEVO: También asignar robot_bombs para colisión sólida
            player._robot_bombs = []
            for enemy in self.enemies:
                if enemy.enemy_type == 'Robot' and hasattr(enemy, 'bombs'):
                    player._robot_bombs.extend(enemy.bombs)
            # FIX: Pasar lista de enemigos para stun al patear bombas
            player._level_enemies = self.enemies
        
        # NUEVO: Preparar lista de jugadores vivos
        all_players_alive = [p for p in self.players if not p.finish]
        
        # PRIMERO: Actualizar estado de colision de TODAS las bombas con TODOS los jugadores
        for bomb in all_bombs:
            bomb.check_all_players_exit(all_players_alive, self.maze.cell_size)
        
        # Actualizar jugadores
        for player in self.players:
            if not player.finish:
                # Verificar pateo de TODAS las bombas con ESTE jugador
                for bomb in all_bombs:
                    bomb.check_kick_collision(player, self.maze)
                
                player.update(dt, self.maze)
                
                # Pasar all_players para raycasting
                player.update_bombs(dt, self.maze, all_players_alive)
            else:
                # Jugador eliminado: sus bombas siguen corriendo hasta explotar
                player.update_bombs(dt, self.maze)
        
        # Recopilar bombas activas de todos los Robots (para evasión de aliados)
        robot_bombs = []
        for e in self.enemies:
            if e.enemy_type == 'Robot':
                robot_bombs.extend(e._active_bombs())

        # NUEVO: Recopilar TODAS las bombas para colisión de enemigos
        all_bombs_for_enemies = []
        for player in self.players:
            all_bombs_for_enemies.extend(player.bombs)
        for e in self.enemies:
            if e.enemy_type == 'Robot' and hasattr(e, 'bombs'):
                all_bombs_for_enemies.extend(e.bombs)
        
        # Asignar _all_bombs a cada enemigo para colisión
        for enemy in self.enemies:
            enemy._all_bombs = all_bombs_for_enemies
            # NUEVO: También asignar _other_bombs para colisión bomba-bomba (Robot)
            if enemy.enemy_type == 'Robot':
                enemy._other_bombs = all_bombs_for_enemies  # Incluye todas las bombas

        # NUEVO: Hacer que enemigos escapen de bombas del Robot
        self._check_enemy_bomb_threats(robot_bombs, dt)

        # Actualizar enemigos: cada uno elige el jugador vivo más cercano
        for enemy in self.enemies[:]:
            # ===== SISTEMA INTELIGENTE: Skip si está escapando =====
            if getattr(enemy, '_skip_normal_update', False):
                # Ya se actualizó en _check_enemy_bomb_threats
                enemy._skip_normal_update = False  # Reset para siguiente frame
                
                # Solo actualizar animación y muerte
                enemy.update_death(dt)
                enemy.animate(dt, moving=(enemy.direction != (0, 0)))
                
                # Aplicar movimiento físico
                enemy.move(dt, self.maze)
                continue
            # ===== FIN SISTEMA INTELIGENTE =====
            
            target = self._nearest_player_to(enemy)
            if target is None:
                continue
            enemy._maze_ref = self.maze   # necesario para _nearby_bomb_danger
            if enemy.enemy_type == 'Snow':
                enemy.update(dt, self.maze, target, self.snow_tiles)
            elif enemy.enemy_type == 'Bear':
                enemy.update(dt, self.maze, target, robot_bombs=robot_bombs)
            elif enemy.enemy_type == 'Robot':
                enemy.update(dt, self.maze, target)   # gestiona su propia evasión
            elif enemy.enemy_type == 'Water':
                enemy.update(dt, self.maze, target)
            elif enemy.enemy_type == 'Globe':
                # Pasar lista de enemigos para powerups
                enemy.update(dt, self.maze, target, self.enemies)
            else:
                enemy.update(dt, self.maze, target)
            
            # Remover enemigos muertos
            if enemy.remove:
                # Drop de llave si este enemigo fue designado como dropper
                if getattr(enemy, '_key_dropper', False):
                    cs     = self.maze.cell_size
                    drop_x = (int(enemy.x + enemy.width  // 2) // cs) * cs
                    drop_y = (int(enemy.y + enemy.height // 2) // cs) * cs
                    self.keys.append(Key((drop_x, drop_y)))

                # Si es un Barrel con pending_spawn, crear el enemigo que escondía
                if enemy.enemy_type == 'Barrel' and getattr(enemy, 'pending_spawn', None):
                    self._spawn_from_barrel(enemy)

                self.enemies.remove(enemy)
                self.enemies_killed += 1
                self.score += enemy.score_value
        
        # Actualizar bombas
        self._update_bombs(dt)
        
        # Actualizar power-ups
        for powerup in self.powerups[:]:
            if powerup.remove:
                self.powerups.remove(powerup)
                continue
            was_collected = powerup.collected
            # Comprobar colisión con TODOS los jugadores vivos
            for player in self.players:
                if not player.dead and not player.finish:
                    powerup.update(dt, player)
                    if powerup.collected and not was_collected:
                        self.audio.play_sfx('powerup_collect')
                        break  # Recogido, no procesar más jugadores
                    if powerup.remove:
                        break
        
        # ── Sync: charcos Water  puddle_tiles  |  enemy_powerups Globe  central ──
        for e in self.enemies:
            if e.enemy_type == 'Water':
                for puddle in e.puddles:
                    if puddle not in self.puddle_tiles:
                        self.puddle_tiles.append(puddle)
            elif e.enemy_type == 'Globe':
                for ep in e.enemy_powerups:
                    if ep not in self.enemy_powerups:
                        self.enemy_powerups.append(ep)

        # Actualizar bloques de nieve
        for snow in self.snow_tiles[:]:
            snow.update(dt)
            if snow.remove:
                self.snow_tiles.remove(snow)

        # Actualizar charcos
        for puddle in self.puddle_tiles[:]:
            puddle.update(dt)
            if puddle.remove:
                self.puddle_tiles.remove(puddle)

        # Actualizar enemy_powerups con verificación de colisiones
        for ep in self.enemy_powerups[:]:
            ep.update(dt)  # Actualiza animación flotante
            
            # Verificar colisión con enemigos vivos (Globe NUNCA recoge powerups)
            if not ep.collected:
                for enemy in self.enemies:
                    if enemy.dead:
                        continue
                    if enemy.enemy_type == 'Globe':
                        continue
                    if enemy.rect.colliderect(ep.rect):
                        ep.apply_to_enemy(enemy)
                        print(f" {enemy.enemy_type} recogió powerup '{ep.type}'")
                        break
            
            # Remover si fue recogido
            if ep.collected:
                self.enemy_powerups.remove(ep)

        # Sistema de llaves
        self._update_keys(dt)

        # Verificar ralentización por nieve
        for player in self.players:
            player.check_snow_slowdown(self.snow_tiles)

        # Colisiones (incluye charcos)
        self._check_collisions()

        # Puerta
        self._update_door()

        # Actualizar cámara
        self.camera.update(self.players, dt)
    
    def _update_bombs(self, dt):
        """
        Actualiza las bombas de todos los jugadores y enemigos.
        
        IMPORTANTE: NO llama a bomb.update() aquí (lo hace player.update_bombs())
        Solo maneja explosiones y pasa other_bombs para colisiones
        """
        # Recopilar TODAS las bombas activas del nivel
        all_bombs = []
        for player in self.players:
            all_bombs.extend(player.bombs)
        for enemy in self.enemies:
            if enemy.enemy_type == 'Robot' and hasattr(enemy, 'bombs'):
                all_bombs.extend(enemy.bombs)
        
        # Procesar explosiones de bombas de jugadores
        for player in self.players:
            for bomb in player.bombs:
                if bomb.exploded and bomb.explosion_rects and not bomb.hits_applied:
                    bomb.hits_applied = True
                    self._check_bomb_hits(bomb)
    
        # Bombas de Robots: timer + explosión + permitir pateo de jugadores
        for enemy in self.enemies:
            if enemy.enemy_type != 'Robot':
                continue
            for bomb in enemy.bombs[:]:
                # Permitir que los jugadores pateen la bomba del Robot
                for player in self.players:
                    if not player.dead:
                        bomb.check_player_exit(player, self.maze.cell_size)
                        if not bomb.is_being_kicked and not bomb.is_being_pushed:
                            bomb.try_kick(player, self.maze.cell_size)
                if bomb.exploded and bomb.explosion_rects and not bomb.hits_applied:
                    bomb.hits_applied = True
                    self._check_bomb_hits(bomb)
                if bomb.remove:
                    enemy.bombs.remove(bomb)
                    enemy._active_count = max(0, enemy._active_count - 1)

    def _check_bomb_hits(self, bomb):
        self.audio.play_sfx('bomb_explode')
        """
        Verifica impactos de una explosión de bomba.
        
        Args:
            bomb: La bomba que explotó
        """
        # Destruir ladrillos y generar power-ups
        for explosion_rect, direction, is_end in bomb.explosion_rects:
            cell_col = explosion_rect.x // CELL_SIZE
            cell_row = explosion_rect.y // CELL_SIZE
            
            # Verificar límites
            if not (0 <= cell_row < MAP_ROWS and 0 <= cell_col < MAP_COLS):
                continue
            
            # Destruir ladrillo
            if self.maze.grid[cell_row][cell_col] == 'brick':
                self.maze.grid[cell_row][cell_col] = 'empty'
                self.score += 10
                
                # Intentar generar power-up
                powerup = try_drop_powerup((cell_col * CELL_SIZE, cell_row * CELL_SIZE))
                if powerup:
                    self.powerups.append(powerup)
        
        # Verificar daño a enemigos
        # CORREGIDO: Todas las bombas dañan a todos los enemigos (incluido Robot)
        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            for explosion_rect, direction, is_end in bomb.explosion_rects:
                if enemy_rect.colliderect(explosion_rect):
                    enemy.take_damage(1)
                    break
        
        # Verificar daño a jugadores
        for player in self.players:
            if player.dead or player.invincibility_timer > 0:
                continue
            for explosion_rect, _, __ in bomb.explosion_rects:
                if player.rect.colliderect(explosion_rect):
                    player.hit = True
                    break
    
    def _nearest_player_to(self, entity):
        """
        Retorna el jugador vivo más cercano a una entidad específica.
        Cada enemigo llama a este método para elegir su propio target.
        Si no hay jugadores vivos, retorna None (el enemigo no se mueve).
        """
        alive = [p for p in self.players if not p.dead and not p.finish]
        if not alive:
            return None
        if len(alive) == 1:
            return alive[0]
        return min(alive,
                   key=lambda p: (p.x - entity.x) ** 2 + (p.y - entity.y) ** 2)

    def _nearest_alive_player(self):
        """
        Retorna cualquier jugador vivo (alias para retrocompatibilidad).
        Prefiere usar _nearest_player_to(entity) cuando sea posible.
        """
        alive = [p for p in self.players if not p.dead and not p.finish]
        return alive[0] if alive else (self.players[0] if self.players else None)

    def _update_keys(self, dt):
        """
        1ª vez: asigna N enemigos aleatorios como droppers (N = num_players).
        Cada frame: actualiza llaves en el suelo y detecta recogida.
        """
        alive = [e for e in self.enemies if not e.dead and not e.remove]

        if not self._key_enemies_assigned and alive:
            n      = self.num_players
            sample = random.sample(alive, min(n, len(alive)))
            for e in sample:
                e._key_dropper = True
            self._key_enemies_assigned = True

        # Reasignar si el dropper murió antes de poder dropear y quedan enemigos
        pending = sum(1 for p in self.players if not getattr(p, 'has_key', False))                   - len(self.keys)
        if pending > 0 and alive:
            active_droppers = [e for e in alive if getattr(e, '_key_dropper', False)]
            if not active_droppers:
                sample = random.sample(alive, min(pending, len(alive)))
                for e in sample:
                    e._key_dropper = True

        # Actualizar llaves en suelo
        vivos = [p for p in self.players if not p.dead and not getattr(p, 'finish', False)]
        for key in self.keys[:]:
            key.update(dt, vivos)
            if key.remove:
                self.keys.remove(key)

    def _update_door(self):
        """Abre la puerta cuando todos los jugadores vivos tienen llave.
        Si la puerta está abierta y un jugador la toca  level_complete.
        """
        vivos = [p for p in self.players
                 if not p.dead and not getattr(p, 'finish', False)]
        if not vivos:
            return

        if all(getattr(p, 'has_key', False) for p in vivos) and not self.maze.door_open:
            self.maze.door_open = True

        if self.maze.door_open:
            cs        = self.maze.cell_size
            door_rect = pygame.Rect(self.maze.door_col * cs,
                                    self.maze.door_row * cs,
                                    cs, cs)
            for player in vivos:
                if player.rect.colliderect(door_rect):
                    self.level_complete = True

    def _check_collisions(self):
        """Verifica colisiones entre entidades."""
        for player in self.players:
            if player.dead or player.invincibility_timer > 0:
                continue

            # Colisión con enemigos
            for enemy in self.enemies:
                if enemy.dead:
                    continue
                # Globe invulnerable mientras vuela
                if enemy.enemy_type == 'Globe' and getattr(enemy, 'is_flying', False):
                    continue
                if player.rect.colliderect(enemy.rect):
                    player.hit = True
                    break

            # Colisión con charcos (resbalón)
            if not getattr(player, 'is_slipping', False):
                for puddle in self.puddle_tiles:
                    if not puddle.remove and player.rect.colliderect(puddle.rect):
                        player.is_slipping = True
                        player.slip_timer = WaterConfig.PUDDLE_SLIP_DURATION
                        player.slip_direction = (player.direction
                                                 if player.direction != (0, 0) else (1, 0))
                        player.original_speed = player.speed 
                        break

    # CONDICIONES DE VICTORIA/DERROTA

    def check_gameover(self):
        """Game over cuando TODOS los jugadores han terminado."""
        return self.players and all(p.finish and p.lives <= 0 for p in self.players)
    
    def check_victory(self):
        """Victoria: sin enemigos y al menos un jugador vivo."""
        any_alive = any(not p.dead and not p.finish for p in self.players)
        return len(self.enemies) == 0 and any_alive
    
    
    # DRAW - CON SOPORTE DIAGONAL CELDA POR CELDA
    
    def _draw_entity_with_diagonal(self, entity, screen, camera, viewport_index, vp):
        """
        Dibuja una entidad verificando el clipping diagonal celda por celda.
        
        Args:
            entity: Entidad a dibujar (player, enemy, bomb, etc.)
            screen: Superficie de pantalla
            camera: SplitCamera
            viewport_index: Índice del viewport (0 o 1)
            vp: Viewport actual
        """
        if camera.split_mode != 'diagonal':
            # Sin diagonal, dibujar directamente
            entity.draw(screen, vp)
            return
        
        # Para diagonal, verificar si debe dibujarse
        # Obtener posición en pantalla
        screen_x, screen_y = vp.apply(entity.x, entity.y)
        
        # Verificar si esta posición pertenece a este viewport
        if camera.should_draw_at_position(screen_x, screen_y, viewport_index):
            entity.draw(screen, vp)
    
    def draw(self, screen):
        """Dibuja todo el nivel con soporte diagonal celda por celda."""
        # Fondo
        screen.fill(Colors.BACKGROUND)
        
        # Mapa (ya tiene clipping diagonal integrado)
        self.maze.draw(screen, self.camera)
        
        # Grid (opcional)
        if self.show_grid:
            self._draw_grid(screen)
        
        # Entidades con clipping diagonal
        self._draw_entities(screen)
        
        # UI
        self._draw_ui(screen)
        
        # Debug
        if self.show_debug:
            self._draw_debug(screen)
        
        # Hitboxes
        if self.show_hitbox:
            self._draw_hitboxes(screen)
    
    def _draw_entities(self, screen):
        """Dibuja entidades con soporte para diagonal celda por celda."""
        if isinstance(self.camera, SplitCamera) and self.camera.split_mode == 'diagonal':
            # MODO DIAGONAL: Dibujar celda por celda
            for viewport_index, (surf, vp, flag) in enumerate(self.camera.iter_viewports(screen)):
                # Charcos (capa más baja)
                for puddle in self.puddle_tiles:
                    if not puddle.remove:
                        self._draw_entity_with_diagonal(puddle, surf, self.camera, viewport_index, vp)
                # Snow tiles
                for snow in self.snow_tiles:
                    self._draw_entity_with_diagonal(snow, surf, self.camera, viewport_index, vp)
                # Power-ups jugadores
                for powerup in self.powerups:
                    self._draw_entity_with_diagonal(powerup, surf, self.camera, viewport_index, vp)
                # Enemy powerups Globe
                for ep in self.enemy_powerups:
                    if not ep.collected:
                        self._draw_entity_with_diagonal(ep, surf, self.camera, viewport_index, vp)
                # Llaves
                for key in self.keys:
                    if not key.collected:
                        self._draw_entity_with_diagonal(key, surf, self.camera, viewport_index, vp)
                
                # Bombas de jugadores
                for player in self.players:
                    for bomb in player.bombs:
                        self._draw_entity_with_diagonal(bomb, surf, self.camera, viewport_index, vp)
                
                # Bombas de robots
                for enemy in self.enemies:
                    if hasattr(enemy, 'bombs'):
                        for bomb in enemy.bombs:
                            self._draw_entity_with_diagonal(bomb, surf, self.camera, viewport_index, vp)
                
                # Enemigos
                for enemy in self.enemies:
                    self._draw_entity_with_diagonal(enemy, surf, self.camera, viewport_index, vp)
                
                # Jugadores
                for player in self.players:
                    if not player.remove:
                        self._draw_entity_with_diagonal(player, surf, self.camera, viewport_index, vp)
        
        elif isinstance(self.camera, SplitCamera):
            # OTROS MODOS SPLIT: horizontal/vertical/merged
            for surf, vp, _ in self.camera.iter_viewports(screen):
                # Charcos
                for puddle in self.puddle_tiles:
                    if not puddle.remove:
                        puddle.draw(surf, vp)
                # Snow tiles
                for snow in self.snow_tiles:
                    snow.draw(surf, vp)
                # Power-ups jugadores
                for powerup in self.powerups:
                    powerup.draw(surf, vp)
                # Enemy powerups Globe
                for ep in self.enemy_powerups:
                    if not ep.collected:
                        ep.draw(surf, vp)
                # Llaves
                for key in self.keys:
                    if not key.collected:
                        key.draw(surf, vp)
                
                # Bombas de jugadores
                for player in self.players:
                    for bomb in player.bombs:
                        bomb.draw(surf, vp)
                
                # Bombas de robots
                for enemy in self.enemies:
                    if hasattr(enemy, 'bombs'):
                        for bomb in enemy.bombs:
                            bomb.draw(surf, vp)
                
                # Enemigos
                for enemy in self.enemies:
                    enemy.draw(surf, vp)
                
                # Jugadores
                for player in self.players:
                    if not player.remove:
                        player.draw(surf, vp)
        
        else:
            # CÁMARA SIMPLE: Un solo jugador
            # Charcos
            for puddle in self.puddle_tiles:
                if not puddle.remove:
                    puddle.draw(screen, self.camera)
            # Snow tiles
            for snow in self.snow_tiles:
                snow.draw(screen, self.camera)
            # Power-ups jugadores
            for powerup in self.powerups:
                powerup.draw(screen, self.camera)
            # Enemy powerups Globe
            for ep in self.enemy_powerups:
                if not ep.collected:
                    ep.draw(screen, self.camera)
            # Llaves
            for key in self.keys:
                if not key.collected:
                    key.draw(screen, self.camera)
            
            # Bombas de jugadores
            for player in self.players:
                for bomb in player.bombs:
                    bomb.draw(screen, self.camera)
            
            # Bombas de robots
            for enemy in self.enemies:
                if hasattr(enemy, 'bombs'):
                    for bomb in enemy.bombs:
                        bomb.draw(screen, self.camera)
            
            # Enemigos
            for enemy in self.enemies:
                enemy.draw(screen, self.camera)
            
            # Jugadores
            for player in self.players:
                if not player.remove:
                    player.draw(screen, self.camera)
        
        # Línea divisoria (solo para split camera)
        if isinstance(self.camera, SplitCamera):
            self.camera.draw_divider(screen)
    
    def _draw_grid(self, screen):
        """Dibuja el grid del mapa."""
        grid_color = Colors.DEBUG_GRID

        def draw_grid_on_viewport(surf, vp):
            """Dibuja el grid en un viewport específico."""
            if hasattr(vp, 'screen_rect'):
                vw, vh = vp.screen_rect.width, vp.screen_rect.height
            else:
                vw, vh = WINDOW_WIDTH, WINDOW_HEIGHT

            sc2 = max(0, int(vp.x // CELL_SIZE))
            ec2 = min(MAP_COLS, int((vp.x + vw) // CELL_SIZE) + 2)
            sr2 = max(0, int(vp.y // CELL_SIZE))
            er2 = min(MAP_ROWS, int((vp.y + vh) // CELL_SIZE) + 2)

            for col in range(sc2, ec2):
                sx, _ = vp.apply(col * CELL_SIZE, 0)
                pygame.draw.line(surf, grid_color, (int(sx), 0), (int(sx), vh), 1)
            for row in range(sr2, er2):
                _, sy = vp.apply(0, row * CELL_SIZE)
                pygame.draw.line(surf, grid_color, (0, int(sy)), (vw, int(sy)), 1)

        # Dibujar grid en cada viewport
        if isinstance(self.camera, SplitCamera):
            for surf, vp, _ in self.camera.iter_viewports(screen):
                draw_grid_on_viewport(surf, vp)
        else:
            draw_grid_on_viewport(screen, self.camera)
        # UI Y DEBUG (Siempre sin clipping)
        self._draw_ui(screen)
        
        #if self.show_debug:
         #   pygame.draw.line(surf, grid_color, (0, int(sy)), (vw, int(sy)), 1)
    
    def _draw_ui(self, screen):
        """Dibuja la interfaz de usuario para cada jugador."""
        # Nivel y enemigos (centrado)
        draw_text(screen, f"Nivel {self.current_level}",
                  (WINDOW_WIDTH // 2, 10), self.font_small, Colors.WHITE, align='center')
        draw_text(screen, f"Enemigos: {len(self.enemies)}",
                  (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 40), self.font_small, Colors.DEBUG_TEXT)

        # UI por jugador (vidas + score + invencibilidad)
        for i, player in enumerate(self.players):
            self._draw_player_ui(screen, player, slot=i)

    def _draw_player_ui(self, screen, player, slot):
        """Dibuja la UI de un jugador en el slot indicado (0=izq, 1=der...)."""
        from settings import PlayerConfig
        col = slot % 2      # 0izquierda, 1derecha
        row = slot // 2     # 0arriba, 1abajo

        base_x = 20 + col * (WINDOW_WIDTH // 2)
        base_y = 20 + row * 80

        # Fondo semitransparente
        bg = pygame.Surface((180, 70), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, (base_x - 5, base_y - 5))

        # Etiqueta del jugador
        draw_text(screen, player.label,
                  (base_x, base_y), self.font_small, player.ui_color)

        # Corazones
        heart_x = base_x + 30
        for i in range(player.max_lives):
            color = Colors.HEALTH_RED if i < player.lives else (80, 80, 80)
            hx = heart_x + i * 22
            hy = base_y
            pygame.draw.circle(screen, color, (hx + 5, hy + 6), 5)
            pygame.draw.circle(screen, color, (hx + 14, hy + 6), 5)
            pygame.draw.polygon(screen, color,
                                [(hx, hy + 6), (hx + 19, hy + 6), (hx + 9, hy + 19)])

        # Score
        draw_text(screen, f"Score: {player.score}",
                  (base_x, base_y + 25), self.font_small, Colors.DEBUG_TEXT)

        # Indicador de llave 
        has_key = getattr(player, 'has_key', False)
        key_color  = (255, 215, 0) if has_key else (80, 80, 80)
        key_label  = "🗝 LLAVE" if has_key else "🗝 ..."
        draw_text(screen, key_label, (base_x, base_y + 42),
                  self.font_small, key_color)

        # Barra de invencibilidad
        if player.invincibility_timer > 0:
            draw_health_bar(screen, (base_x, base_y + 56),
                            player.invincibility_timer, player.invincibility_duration,
                            width=150, height=8, fill_color=Colors.INVINCIBLE_GOLD)
    
    # _draw_hearts eliminado: reemplazado por _draw_player_ui
    
    def _draw_debug(self, screen):
        """Dibuja información de debug."""
        debug_lines = [
            f"FPS: {int(self.game.clock.get_fps())}",
            "",
            f"Jugadores: {len(self.players)}",
            *[f"  {p.label}: pos({int(p.x)},{int(p.y)}) vidas:{p.lives}"
              for p in self.players],
            "",
            f"Entidades:",
            f"  Enemigos: {len(self.enemies)}",
            f"  Power-ups: {len(self.powerups)}",
            f"  Nieve: {len(self.snow_tiles)}",
        ]
        
        # Fondo semi-transparente
        info_height = len(debug_lines) * 18 + 10
        overlay = pygame.Surface((250, info_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (WINDOW_WIDTH - 260, WINDOW_HEIGHT - info_height - 10))
        
        # Texto
        y = WINDOW_HEIGHT - info_height - 5
        for line in debug_lines:
            if line:
                draw_text(screen, line, (WINDOW_WIDTH - 255, y), 
                         self.font_small, Colors.DEBUG_TEXT)
            y += 18
    
    def _draw_hitboxes(self, screen):
        """Dibuja hitboxes de debug con zoom."""
        zoom = getattr(self.camera, 'zoom', 1.0)

        def scaled_rect(sx, sy, w, h):
            return (int(sx), int(sy), max(1, int(w * zoom)), max(1, int(h * zoom)))

        for player in self.players:
            if not player.remove:
                sx, sy = self.camera.apply(player.rect.x, player.rect.y)
                pygame.draw.rect(screen, player.ui_color,
                                 scaled_rect(sx, sy, player.width, player.height), 2)
            for bomb in player.bombs:
                sx, sy = self.camera.apply(bomb.x, bomb.y)
                pygame.draw.rect(screen, (0, 255, 0),
                                 scaled_rect(sx, sy, bomb.width, bomb.height), 2)

        for enemy in self.enemies:
            sx, sy = self.camera.apply(enemy.x, enemy.y)
            pygame.draw.rect(screen, (255, 255, 0),
                             scaled_rect(sx, sy, enemy.width, enemy.height), 2)
    
    # GENERACIÓN DINÁMICA DE ENEMIGOS
    
    def _get_random_spawn_position(self):
        """
        Busca una posición aleatoria válida para spawnear un enemigo.
        
        FIX BUG #5: Más intentos + verificación explícita + fallback
        
        Returns:
            (x, y) en píxeles o None si no encuentra posición
        """
        # Primer intento: Posición óptima (lejos de jugadores)
        for _ in range(100):  # Aumentado de 50 a 100
            col = random.randint(10, MAP_COLS - 2)
            row = random.randint(2,  MAP_ROWS - 2)
            
            # VERIFICACIÓN EXPLÍCITA: Solo 'empty'
            cell_type = self.maze.grid[row][col]
            if cell_type != 'empty':
                continue
            
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            
            # Distancia al jugador más cercano
            min_dist = min(
                ((x - p.x)**2 + (y - p.y)**2)**0.5
                for p in self.players
            )
            
            if min_dist > 200:
                return (x, y)
        
        # FALLBACK: Buscar CUALQUIER 'empty' sin restricción de distancia
        for _ in range(200):
            col = random.randint(1, MAP_COLS - 2)
            row = random.randint(1, MAP_ROWS - 2)
            
            if self.maze.grid[row][col] == 'empty':
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                return (x, y)
        
        # Último recurso
        return None
    
    def _get_robot_spawn_position(self):
        """
        Posición especial para Robot con zona segura.
        
        FIX BUG #4: Robot necesita zona 3x3 para bomba sin matar aliados
        
        Returns:
            (x, y) en píxeles o None
        """
        for _ in range(100):
            col = random.randint(10, MAP_COLS - 4)
            row = random.randint(2, MAP_ROWS - 4)
            
            # Verificar celda central
            if self.maze.grid[row][col] != 'empty':
                continue
            
            # VERIFICAR ZONA 3x3 ALREDEDOR
            safe_zone = True
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    check_row = row + dr
                    check_col = col + dc
                    
                    if not (0 <= check_row < MAP_ROWS and 0 <= check_col < MAP_COLS):
                        safe_zone = False
                        break
                    
                    cell = self.maze.grid[check_row][check_col]
                    # Permitir 'empty' y 'brick' (los bricks se pueden romper)
                    if cell not in ['empty', 'brick']:
                        safe_zone = False
                        break
                
                if not safe_zone:
                    break
            
            if not safe_zone:
                continue
            
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            
            # Verificar distancia a jugadores
            min_dist = min(
                ((x - p.x)**2 + (y - p.y)**2)**0.5
                for p in self.players
            )
            
            if min_dist > 200:
                return (x, y)
        
        # Fallback: Usar spawn normal
        return self._get_random_spawn_position()

    def _spawn_enemies_dynamic(self, level_number):
        """Genera enemigos dinámicamente según nivel y dificultad."""
        enemy_types = DynamicLevelGenerator.generate_enemy_list(
            level_number,
            self.difficulty_config
        )

        from collections import Counter
        type_counts = Counter(enemy_types)
        print(f"Generando {len(enemy_types)} enemigos:")
        for enemy_type, count in sorted(type_counts.itemás()):
            print(f"   {enemy_type.capitalize()}: {count}")

        for enemy_type in enemy_types:
            # FIX BUG #4: Spawn especial para Robot (zona segura)
            if enemy_type.lower() == 'robot':
                pos = self._get_robot_spawn_position()
            else:
                pos = self._get_random_spawn_position()
            
            if not pos:
                print(f"  No se encontró posición válida para {enemy_type}")
                continue

            enemy = self._create_enemy(enemy_type, pos)
            if enemy:
                self._apply_difficulty_to_enemy(enemy)
                self.enemies.append(enemy)

        print(f"{len(self.enemies)} enemigos creados exitosamente")
    
    def _create_enemy(self, enemy_type, pos):
        """Crea un enemigo del tipo especificado."""
        enemy_classes = {
            'ghost': Ghost,
            'snow': Snow,
            'bear': Bear,
            'barrel': Barrel,
            'robot': Robot,
            'water': Water,
            'globe': Globe
        }
        
        enemy_class = enemy_classes.get(enemy_type)
        if enemy_class:
            return enemy_class(pos)
        else:
            print(f"  Tipo de enemigo desconocido: {enemy_type}")
            return None
    
    def _apply_difficulty_to_enemy(self, enemy):
        """Aplica modificadores de dificultad a un enemigo."""
        original_lives = enemy.lives
        original_speed = enemy.speed

        enemy.lives = DifficultyConfig.get_enemy_lives(
            enemy.enemy_type,
            original_lives,
            self.difficulty_config
        )

        enemy.speed = DifficultyConfig.get_enemy_speed(
            original_speed,
            self.difficulty_config
        )

        # Aplicar reaction_multiplier: escala el tiempo de reaccion a bombas
        # FACIL=1.6x (mas lento), NORMAL=1.0x, DIFICIL=0.5x (mas rapido)
        react_mult = self.difficulty_config.get('reaction_multiplier', 1.0)
        if hasattr(enemy, '_bomb_reaction_time'):
            enemy._bomb_reaction_time = enemy._bomb_reaction_time * react_mult

        if enemy.lives != original_lives or abs(enemy.speed - original_speed) > 0.1:
            print(f"   └─ {enemy.enemy_type}: "
                  f"vidas {original_lives}{enemy.lives}, "
                  f"velocidad {original_speed:.0f}{enemy.speed:.0f}, "
                  f"reaccion_bomba={getattr(enemy, '_bomb_reaction_time', 'n/a'):.1f}s")
    
    # CLEANUP
    
    def cleanup(self):
        """Limpia recursos del nivel."""
        self.players.clear()
        self.enemies.clear()
        self.bombs.clear()
        self.powerups.clear()
        self.snow_tiles.clear()
        print("Level Manager limpiado")