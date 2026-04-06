"""
SETTINGS.PY - Configuración Global del Juego
=============================================

Archivo central de configuración que contiene todas las constantes,
parámetros y ajustes del juego. Facilita balanceo y modificación
sin tocar el código principal.

Contenido:
----------

1. Rutas y Directorios:
   - BASE_DIR: Directorio raíz del proyecto
   - IMAGES_DIR: Carpeta de sprites (assets/images/)
   - SOUNDS_DIR: Carpeta de efectos (assets/sounds/)
   - MUSIC_DIR: Carpeta de música (assets/music/)

2. Ventana y Display:
   - WINDOW_WIDTH, WINDOW_HEIGHT: Tamaño de ventana (1250x700)
   - WINDOW_TITLE: Título de la ventana
   - FPS: Frames por segundo (60)

3. Mapa:
   - CELL_SIZE: Tamaño de celda (32px)
   - MAP_COLS, MAP_ROWS: Dimensiones del mapa (70x30)
   - MAP_WIDTH, MAP_HEIGHT: Dimensiones en píxeles
   - CAMERA_WIDTH, CAMERA_HEIGHT: Tamaño del viewport

4. Colores (Colors):
   Clase con constantes de colores RGB:
   - Básicos: WHITE, BLACK, RED, GREEN, BLUE
   - UI: MENU_BG, MENU_SELECTED, TEXT_COLOR
   - Gameplay: HEALTH_RED, HEALTH_BG, DOOR_OPEN
   - Debug: DEBUG_HITBOX, DEBUG_PATH

5. Estados del Juego (GameStates):
   Enum con estados posibles:
   - MENU: Menú principal
   - PLAYER_SELECT: Selección de jugadores
   - DIFFICULTY_SELECT: Selección de dificultad
   - PLAYING: Jugando
   - PAUSED: Pausado
   - GAMEOVER: Derrota
   - VICTORY: Victoria

6. Configuración de Entidades:
   
   BombermanConfig:
   - SPEED: Velocidad de movimiento (120)
   - LIVES: Vidas iniciales (3)
   - ANIMATION_SPEED: Velocidad de animación
   
   BombConfig:
   - FUSE_TIME: Tiempo de explosión (3s)
   - BASE_RANGE: Alcance base (2 celdas)
   - KICK_SPEED: Velocidad de pateo (200)
   - MAX_KICK_DISTANCE: Distancia máxima de pateo
   
   GhostConfig, SnowConfig, BearConfig, etc.:
   - SPEED: Velocidad del enemigo
   - LIVES: Resistencia
   - DETECTION_RANGE: Rango de detección
   - Parámetros específicos de habilidad

7. Sistema de Dificultad (DifficultyConfig):
   Multiplicadores por dificultad:
   - EASY: 0.8x velocidad enemigos, 1.2x vida jugador
   - NORMAL: 1.0x valores por defecto
   - HARD: 1.3x velocidad enemigos, 0.8x vida jugador
   - EXPERT: 1.5x velocidad, 0.5x vida

8. Controles (Controls):
   Mapeo de teclas por jugador:
   - PLAYER_1: Flechas + Espacio
   - PLAYER_2: WASD + E
   - PLAYER_3: IJKL + U
   - PLAYER_4: Numpad + Num0
   
   Botones de gamepad también soportados.

9. Configuración de Jugador (PlayerConfig):
   - SPAWN_OFFSETS: Posiciones iniciales por jugador
   - PLAYER_COLORS: Colores por jugador (tint)
   - MAX_PLAYERS: Cantidad máxima (4)

10. Power-ups (PowerUpConfig):
    - DROP_CHANCE: Probabilidad de drop (0.4 = 40%)
    - POWERUP_WEIGHTS: Peso de cada tipo de power-up
    - DURATION: Duración de efectos temporales

11. Audio (AudioConfig):
    - MASTER_VOLUME: Volumen maestro (0.0-1.0)
    - MUSIC_VOLUME: Volumen de música
    - SFX_VOLUME: Volumen de efectos
    - MUSIC_ENABLED, SFX_ENABLED: Activar/desactivar
    
    MUSIC_TRACKS: Dict de pistas de música
    - 'menu': Música del menú
    - 'level_1', 'level_2': Música de niveles
    - 'victory', 'gameover': Música de fin
    
    SOUND_EFFECTS: Dict de efectos de sonido
    - 'bomb_place', 'explosion': Bombas
    - 'powerup', 'death': Eventos
    - 'door_open', 'key': Progresión

12. Sistema de Niveles (LevelConfig):
    Configuración por nivel:
    - enemy_spawn_count: Cantidad de enemigos
    - enemy_types: Tipos de enemigos permitidos
    - brick_density: Densidad de bricks (0.0-1.0)
    - Escalado de dificultad por nivel

Funciones Auxiliares:
---------------------

validate_settings():
    Valida que todas las configuraciones sean coherentes.
    Lanza ValueError si detecta problemas.
    
    Verifica:
    - Dimensiones de mapa divisibles por CELL_SIZE
    - Valores de configuración en rangos válidos
    - Existencia de archivos de audio/imágenes críticos

get_config_summary():
    Retorna string con resumen de configuración actual.
    Útil para debugging y logging.
    
    Formato:
        Mapa: 70x30 (2240x960px)
        Cámara: 1250x700
        FPS: 60

apply_difficulty_multiplier(base_value, stat_type, difficulty):
    Aplica multiplicador de dificultad a un valor.
    
    Args:
        base_value: Valor base
        stat_type: 'speed', 'health', 'damage', etc.
        difficulty: 'EASY', 'NORMAL', 'HARD', 'EXPERT'
    
    Returns:
        Valor modificado según dificultad

Uso típico:
-----------
    from settings import (
        CELL_SIZE, MAP_ROWS, MAP_COLS,
        BombermanConfig, BombConfig,
        Colors, GameStates
    )
    
    # Acceder a configuración
    player_speed = BombermanConfig.SPEED
    bomb_fuse = BombConfig.FUSE_TIME
    
    # Aplicar dificultad
    enemy_speed = apply_difficulty_multiplier(
        GhostConfig.SPEED, 
        'speed', 
        'HARD'
    )
    
    # Validar al inicio
    validate_settings()

Modificación:
-------------
Para cambiar parámetros del juego, simplemente edita los valores
en este archivo. No es necesario tocar el código de gameplay.

Ejemplo - Hacer bombas más rápidas:
    BombConfig.FUSE_TIME = 2.0  # era 3.0

Ejemplo - Más enemigos por nivel:
    LevelConfig.LEVELS[1]['enemy_spawn_count'] = 8  # era 5
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
SOUNDS_DIR = os.path.join(BASE_DIR, 'sounds')
MUSIC_DIR = os.path.join(BASE_DIR, 'music')

WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 700
WINDOW_TITLE = "Bomberman - Clone by Alego"
FPS = 60


CELL_SIZE = 32
MAP_COLS = 70
MAP_ROWS = 30
MAP_WIDTH = MAP_COLS * CELL_SIZE
MAP_HEIGHT = MAP_ROWS * CELL_SIZE

CAMERA_WIDTH = WINDOW_WIDTH
CAMERA_HEIGHT = WINDOW_HEIGHT
CAMERA_SMOOTH = True
CAMERA_SPEED = 10

class Colors:
    BACKGROUND = (50, 50, 50)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    
    HEALTH_RED = (255, 50, 50)
    HEALTH_BG = (100, 100, 100)
    INVINCIBLE_GOLD = (255, 215, 0)
    
    DEBUG_TEXT = (255, 255, 0)
    DEBUG_HITBOX = (255, 0, 0)
    DEBUG_GRID = (80, 80, 80)
    DEBUG_PATH = (0, 255, 0)
    
    PAUSE_OVERLAY = (0, 0, 0, 180)
    GAMEOVER_OVERLAY = (0, 0, 0, 200)
    
    EXPLOSION_ORANGE = (255, 150, 0)
    SNOW_BLUE = (150, 200, 255)
    GHOST_AURA = (200, 200, 255)

class PlayerConfig:
    MAX_PLAYERS = 4

    SPAWN_OFFSETS = {
        1: (1, 1),
        2: (1, MAP_ROWS - 2),
        3: (2, 1),
        4: (2, 2),
    }

    TINTS = {
        1: None,              
        2: None,              
        3: (50, 220, 50),     
        4: (230, 130, 30),    
    }

    SPRITE_PREFIX = {
        1: '',            
        2: 'red_',        
        3: '',            
        4: '',            
    }

    
    LABELS = {1: 'P1', 2: 'P2', 3: 'P3', 4: 'P4'}

    
    UI_COLORS = {
        1: (100, 150, 255),   
        2: (255, 80,  80),    
        3: (80,  220, 80),    
        4: (255, 165, 50),    
    }


class BombermanConfig:
    SPRITE_WIDTH = 24
    SPRITE_HEIGHT = 32
    
    HITBOX_WIDTH = 20
    HITBOX_HEIGHT = 24
    HITBOX_OFFSET_X = (SPRITE_WIDTH - HITBOX_WIDTH) // 2  # 2
    HITBOX_OFFSET_Y = (SPRITE_HEIGHT - HITBOX_HEIGHT) // 2  # 2
    
    MAX_LIVES = 5
    STARTING_LIVES = 5
    BASE_SPEED = 200
    
    INVINCIBILITY_DURATION = 2.0
    
    DEATH_DURATION = 1.5
    
    ANIMATION_SPEED = 10

class BombConfig:
    SIZE = 32
    
    FUSE_TIME = 5.0
    EXPLOSION_DURATION = 0.8

    BASE_RANGE = 2
    MAX_RANGE = 7
    
    KICK_SPEED = 300
    MAX_KICK_DISTANCE = 3 * CELL_SIZE
    
    # Duración del stun al golpear enemigo con bomba pateada/empujada
    KICK_STUN_DURATION = 2.0  # segundos
    
    ANIMATION_SPEED = 10

class EnemyConfig:
    SIZE = 32
    
    INVINCIBILITY_DURATION = 1.0
    
    DEATH_DURATION = 1.5
    
    ANIMATION_SPEED = 5
    
    RANDOM_WALK_INTERVAL = 0.5

class GhostConfig:
    SPEED = 100
    DETECTION_RANGE = 14
    LIVES = 1
    SCORE = 150
    
    GHOST_MODE_DURATION = 2.0
    GHOST_MODE_COOLDOWN = 10.0
    BOMB_REACTION_TIME = 0.8   # s hasta percibir bomba del jugador

class SnowConfig:
    SPEED = 60
    DETECTION_RANGE = 16
    LIVES = 2
    SCORE = 150
    
    SNOW_TRAIL_INTERVAL = 0.5
    SNOW_LIFETIME = 35.0
    SNOW_SLOW_FACTOR = 0.5
    
    FROZEN_COMBO_ENABLED = True
    BOMB_REACTION_TIME = 0.8

class BearConfig:
    SPEED = 90
    DETECTION_RANGE = 20
    LIVES = 5
    SCORE = 500
    
    SNIFF_INTERVAL = 8.0
    SNIFF_DURATION = 2.0
    BREAK_COOLDOWN = 1.0
    BRICK_HITS_TO_BREAK = 2
    BOMB_REACTION_TIME = 0.8

class BarrelConfig:
    SPEED = 40
    DETECTION_RANGE = 16
    LIVES = 2
    SCORE = 100

    SPAWN_COUNT = 1
    STUN_DURATION = 1.5
    SPAWN_PROBABILITIES = {
        'ghost': 0.30,
        'snow':  0.25,
        'bear':  0.25,
        'water': 0.2
    }
    BOMB_REACTION_TIME = 1.0   # lento para percibir

class RobotConfig:
    SPEED             = 115
    LIVES             = 2
    SCORE             = 800
    DETECTION_RANGE   = 999

    BOMB_RANGE        = 2
    MAX_BOMBS         = 1  
    BOMB_COOLDOWN     = 4.5
    BOMB_PLACE_RANGE  = 3  

    GPS_ACTIVE_TIME   = 4.0
    GPS_INACTIVE_TIME = 12.0
    GPS_KEEP_ON_RANGE = 6

    ESCAPE_RADIUS     = 4

    KICK_ALIGN_RANGE  = 5


class PowerUpConfig:
    SIZE = 32
    
    DROP_CHANCE = 0.55
    
    FLOAT_SPEED = 2.0
    
    PROBABILITIES = {
        'extra_life': 0.15,   
        'speed_boost': 0.20,  
        'bomb_range': 0.25,   
        'extra_bomb': 0.20,   
        'invincibility': 0.10,
        'mystery': 0.10
    }
    
    SPEED_BOOST_AMOUNT = 30
    MAX_SPEED = 380          
    INVINCIBILITY_TIME = 10.0


class WaterConfig:
    """Configuración del enemigo Water - Teletransportador"""
    SPEED = 55
    DETECTION_RANGE = 15
    LIVES = 1
    SCORE = 250
    
    # Teletransporte
    TELEPORT_COOLDOWN = 5.0        # Segundos entre teletransportes
    TELEPORT_MAX_DISTANCE = 6      # Celdas máximas al JUGADOR en modo agresivo
    TELEPORT_MIN_DISTANCE = 4      # Celdas mínimas para no aparecer encima
    TELEPORT_CHASE_RANGE  = 10     # Si dist <= esto → modo agresivo cerca del jugador
                                   # Si dist >  esto → salto aleatorio desde posición propia
    TELEPORT_ANIMATION_TIME = 0.3  # Duración de animación desaparición/aparición
    
    # Charcos resbaladizos
    PUDDLE_DROP_INTERVAL = 0.5     # Cada cuánto deja un charco
    PUDDLE_LIFETIME = 12.0         # Duración del charco
    PUDDLE_SLIP_DURATION = 1.5     # Tiempo que resbala el jugador
    PUDDLE_SLIP_SPEED = 250        # Velocidad mientras resbala

    FROZEN_FREEZE_DURATION = 3.0    # Duración del entumecimiento después de salir
    FROZEN_SLOW_FACTOR = 0.3 
    BOMB_REACTION_TIME = 0.8


class GlobeConfig:
    """Configuración del enemigo Globe - Proveedor Volador"""
    SPEED = 95
    DETECTION_RANGE = 14
    LIVES = 1
    SCORE = 350
    
    # Vuelo
    FLY_INTERVAL = 15.0             # Cada cuánto se eleva
    FLY_DURATION = 2.0             # Cuánto tiempo está volando
    FLY_HEIGHT = 32                # Altura visual del vuelo (1 celda)
    SHADOW_ALPHA = 100             # Transparencia de la sombra
    
    # Powerups para enemigos
    POWERUP_DROP_INTERVAL = 20.0    # Cada cuánto suelta powerup
    POWERUP_TYPES = {
        'speed_boost': 0.4,        # 40% probabilidad
        'health_boost': 0.3,       # 30% probabilidad 
        'armor': 0.3               # 30% probabilidad
    }
    
    # Efectos de powerups
    SPEED_BOOST_AMOUNT = 30        # +30 velocidad
    SPEED_BOOST_DURATION = 8.0     # Duración del boost
    HEALTH_BOOST_AMOUNT = 1        # +1 vida
    ARMOR_DURATION = 5.0          # Duración de armadura
    BOMB_REACTION_TIME = 1.0

class AudioConfig:
    MASTER_VOLUME = 0.2
    MUSIC_VOLUME = 0.2
    SFX_VOLUME = 0.1
    
    MUSIC_ENABLED = True
    SFX_ENABLED = True

SOUND_EFFECTS = {
    'bomb_place':       'put_bomb.wav',
    'bomb_explode':     'explosion.wav',
    'powerup_collect':  'power.wav',
    'player_hit':       'lose.wav',
    'player_death':     'just-died.wav',
    'menu_select':      'menu_select.wav',
    'walking':          'walk.wav',
}

MUSIC_TRACKS = {
    'menu':             'title.wav',
    'start':            'start.wav',
    'level_1':          'stage_theme.wav',
    'level_complete':   'level_complete.wav',
    'gameover':         'game_over.wav',
}

class MultiCameraConfig:
    PADDING = 80

    MIN_ZOOM = 0.45

    MAX_ZOOM = 1.0

    ZOOM_LERP = 2.5

    POS_LERP = 5.0

    SPLIT_THRESHOLD = 200

class GameStates:
    MENU = "MENU"
    DIFFICULTY_SELECT = "DIFFICULTY_SELECT"
    PLAYER_SELECT = "PLAYER_SELECT"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAMEOVER = "GAMEOVER"
    VICTORY = "VICTORY"
    LEVEL_TRANSITION = "LEVEL_TRANSITION"

class LevelConfig:
    """
    Configuración base de enemigos por nivel (para dificultad NORMAL).
    El sistema de dificultad multiplica estos valores.
    
    EASY: x0.6 de estos valores
    NORMAL: x1.0 (estos valores exactos)
    HARD: x1.5 de estos valores
    """
    ENEMIES_PER_LEVEL = {
        1: {
            'ghost': 4,
            'snow': 3,
            'bear': 4,
            'barrel': 3,
            'robot': 6,
            'water': 2,
            'globe': 3,
        },
        2: {
            'ghost': 3,
            'snow': 3,
            'bear': 1,
            'barrel': 2,
            'robot': 1,
            'water': 1,
            'globe': 0,
        },
        3: {
            'ghost': 4,
            'snow': 4,
            'bear': 2,
            'barrel': 2,
            'robot': 2,
            'water': 1,
            'globe': 1,
        },
        4: {
            'ghost': 5,
            'snow': 5,
            'bear': 3,
            'barrel': 3,
            'robot': 3,
            'water': 2,
            'globe': 1,
        },
        5: {
            'ghost': 6,
            'snow': 6,
            'bear': 4,
            'barrel': 4,
            'robot': 4,
            'water': 2,
            'globe': 2,
        },
    }
    
    BRICK_DENSITY = 0.15
    MIN_SAFE_ZONE = 7


# SISTEMA DE DIFICULTAD

class DifficultyConfig:
    """
    Configuración de dificultades del juego.
    Afecta: enemigos, jugador, powerups, mapa.
    """
    
    DIFFICULTIES = ['FÁCIL', 'NORMAL', 'DIFÍCIL']
    DEFAULT = 'NORMAL'
    
    # FÁCIL - Para principiantes
    EASY = {
        'name': 'FÁCIL',
        'description': 'Perfecto para aprender',
        'reaction_multiplier': 1.6,  # enemigos reaccionan más lento
        
        # Jugador
        'player_lives': 6,
        'player_speed_bonus': 1.1,
        
        # Enemigos
        'enemy_count_multiplier': 0.6,
        'enemy_speed_multiplier': 0.75,
        'enemy_lives_multiplier': 0.5,
        
        # Distribución (suma 100%)
        'enemy_distribution': {
            'snow': 40,
            'ghost': 25,
            'barrel': 20,
            'bear': 10,
            'water': 5,
            'globe': 0,
            'robot': 0
        },
        
        # Powerups y mapa
        'powerup_drop_chance': 0.7,
        'brick_density_multiplier': 0.8,
        'bomb_range_bonus': 1,
    }
    
    # NORMAL - Balanceado
    NORMAL = {
        'name': 'NORMAL',
        'description': 'Experiencia balanceada',
        'reaction_multiplier': 1.0,
        
        'player_lives': 5,
        'player_speed_bonus': 1.0,
        
        'enemy_count_multiplier': 1.0,
        'enemy_speed_multiplier': 1.0,
        'enemy_lives_multiplier': 1.0,
        
        'enemy_distribution': {
            'snow': 20,
            'ghost': 20,
            'barrel': 15,
            'bear': 15,
            'water': 15,
            'globe': 10,
            'robot': 5
        },
        
        'powerup_drop_chance': 0.55,
        'brick_density_multiplier': 1.0,
        'bomb_range_bonus': 0,
    }
    
    # DIFÍCIL - Para expertos
    HARD = {
        'name': 'DIFÍCIL',
        'description': '¡Solo para expertos!',
        'reaction_multiplier': 0.5,  # reaccionan el doble de rapido
        
        'player_lives': 4,
        'player_speed_bonus': 0.95,
        
        'enemy_count_multiplier': 1.5,
        'enemy_speed_multiplier': 1.25,
        'enemy_lives_multiplier': 1.5,
        
        'enemy_distribution': {
            'snow': 10,
            'ghost': 15,
            'barrel': 20,
            'bear': 15,
            'water': 15,
            'globe': 10,
            'robot': 15
        },
        
        'powerup_drop_chance': 0.4,
        'brick_density_multiplier': 1.3,
        'bomb_range_bonus': 0,
    }
    
    @staticmethod
    def get_config(difficulty_name):
        """Obtiene la configuración de una dificultad."""
        configs = {
            'FÁCIL': DifficultyConfig.EASY,
            'NORMAL': DifficultyConfig.NORMAL,
            'DIFÍCIL': DifficultyConfig.HARD
        }
        return configs.get(difficulty_name, DifficultyConfig.NORMAL)
    
    @staticmethod
    def get_enemy_lives(enemy_type, base_lives, difficulty_config):
        """Calcula vidas de enemigo según dificultad (mínimo 1)."""
        multiplier = difficulty_config['enemy_lives_multiplier']
        adjusted = int(base_lives * multiplier)
        return max(1, adjusted)
    
    @staticmethod
    def get_enemy_speed(base_speed, difficulty_config):
        """Calcula velocidad de enemigo según dificultad."""
        return base_speed * difficulty_config['enemy_speed_multiplier']


class DynamicLevelGenerator:
    """Genera enemigos dinámicamente según nivel y dificultad."""
    
    # Cantidad base de enemigos por nivel (NORMAL)
    BASE_ENEMY_COUNTS = {
        1: 8,
        2: 12,
        3: 16,
        4: 20,
        5: 25,
    }
    
    @staticmethod
    def generate_enemy_list(level_number, difficulty_config):
        """
        Genera lista de tipos de enemigos.
        
        Returns:
            list: ['snow', 'ghost', 'bear', ...]
        """
        import random
        
        # Cantidad total según nivel y dificultad
        base_count = DynamicLevelGenerator.BASE_ENEMY_COUNTS.get(level_number, 10)
        multiplier = difficulty_config['enemy_count_multiplier']
        total_enemies = int(base_count * multiplier)
        
        # Distribución de tipos
        distribution = difficulty_config['enemy_distribution']
        
        # Crear pool ponderado
        enemy_pool = []
        for enemy_type, weight in distribution.items():
            count = int(total_enemies * (weight / 100.0))
            enemy_pool.extend([enemy_type] * count)
        
        # Ajustar si falta por redondeo
        while len(enemy_pool) < total_enemies:
            most_common = max(distribution, key=distribution.get)
            enemy_pool.append(most_common)
        
        # Mezclar aleatoriamente
        random.shuffle(enemy_pool)
        
        return enemy_pool[:total_enemies]
    
    @staticmethod
    def get_level_brick_density(level_number, difficulty_config):
        """Calcula densidad de ladrillos según nivel y dificultad."""
        base_density = {
            1: 0.15,
            2: 0.18,
            3: 0.20,
            4: 0.22,
            5: 0.25
        }
        
        base = base_density.get(level_number, 0.18)
        multiplier = difficulty_config['brick_density_multiplier']
        
        return min(0.35, base * multiplier)  # Máximo 35%


class DebugConfig:
    SHOW_FPS = True
    SHOW_HITBOXES = False
    SHOW_GRID = False
    SHOW_PATHFINDING = False
    
    LOG_COLLISIONS = False
    LOG_PATHFINDING = False
    LOG_STATE_CHANGES = True

import pygame

class Controls:
    PAUSE       = pygame.K_ESCAPE
    RESET       = pygame.K_r

    TOGGLE_DEBUG  = pygame.K_d
    TOGGLE_GRID   = pygame.K_g
    TOGGLE_HITBOX = pygame.K_b
    TOGGLE_PATH   = pygame.K_p

    MENU_SELECT = pygame.K_RETURN
    MENU_UP     = pygame.K_UP
    MENU_DOWN   = pygame.K_DOWN

    class PLAYER1:
        UP    = pygame.K_UP
        DOWN  = pygame.K_DOWN
        LEFT  = pygame.K_LEFT
        RIGHT = pygame.K_RIGHT
        BOMB  = pygame.K_SPACE

    class PLAYER2:
        UP    = pygame.K_w
        DOWN  = pygame.K_s
        LEFT  = pygame.K_a
        RIGHT = pygame.K_d
        BOMB  = pygame.K_f

    class PLAYER3:
        UP    = pygame.K_i
        DOWN  = pygame.K_k
        LEFT  = pygame.K_j
        RIGHT = pygame.K_l
        BOMB  = pygame.K_u

    class PLAYER4:
        UP    = pygame.K_KP8
        DOWN  = pygame.K_KP5
        LEFT  = pygame.K_KP4
        RIGHT = pygame.K_KP6
        BOMB  = pygame.K_KP0

    BY_PLAYER = {}

Controls.BY_PLAYER = {
    1: Controls.PLAYER1,
    2: Controls.PLAYER2,
    3: Controls.PLAYER3,
    4: Controls.PLAYER4,
}

def get_config_summary():
    return f"""
    ╔════════════════════════════════════════╗
    ║  BOMBERMAN - CONFIGURACIÓN DEL JUEGO   ║
    ╠════════════════════════════════════════╣
    ║  Ventana: {WINDOW_WIDTH}x{WINDOW_HEIGHT}                     ║
    ║  FPS: {FPS}                               ║
    ║  Mapa: {MAP_COLS}x{MAP_ROWS} celdas                    ║
    ║  Celda: {CELL_SIZE}x{CELL_SIZE}                          ║
    ╚════════════════════════════════════════╝
    """

def validate_settings():
    errors = []
    
    if WINDOW_WIDTH > MAP_WIDTH:
        errors.append(f"WINDOW_WIDTH ({WINDOW_WIDTH}) > MAP_WIDTH ({MAP_WIDTH})")
    
    if WINDOW_HEIGHT > MAP_HEIGHT:
        errors.append(f"WINDOW_HEIGHT ({WINDOW_HEIGHT}) > MAP_HEIGHT ({MAP_HEIGHT})")
    
    total_prob = sum(PowerUpConfig.PROBABILITIES.values())
    if abs(total_prob - 1.0) > 0.01:
        errors.append(f"Probabilidades de power-ups suman {total_prob}, deberían sumar 1.0")
    
    if not os.path.exists(IMAGES_DIR):
        errors.append(f"Directorio de imágenes no existe: {IMAGES_DIR}")
    
    if errors:
        print("!!!  ADVERTENCIAS DE CONFIGURACIÓN:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("Configuración validada correctamente")
        return True

if __name__ == "__main__":
    print(get_config_summary())
    validate_settings()