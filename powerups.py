"""
Sistema de powerups coleccionables del juego.

Este módulo implementa todos los tipos de powerups que pueden aparecer
al destruir ladrillos. Cada powerup otorga una mejora permanente o
temporal al jugador que lo recoge.

Powerups Implementados:
    - BombPowerup: +1 bomba máxima simultánea
    - FlamePowerup: +1 rango de explosión
    - SpeedPowerup: +20% velocidad de movimiento
    - KickPowerup: Habilidad de patear bombas
    - WallPassPowerup: Atravesar ladrillos (temporal)
    - BombPassPowerup: Atravesar bombas (temporal)
    - FlamePassPowerup: Inmunidad a explosiones (temporal)
    - MysteryPowerup: Powerup aleatorio (cualquiera de los anteriores)

Clases Exportadas:
    - Powerup: Clase base abstracta
    - BombPowerup, FlamePowerup, SpeedPowerup: Mejoras permanentes
    - KickPowerup: Habilidad de pateo
    - WallPassPowerup, BombPassPowerup, FlamePassPowerup: Temporales
    - MysteryPowerup: Powerup aleatorio

Uso Típico:
    # Spawn al destruir ladrillo
    powerup = random.choice([
        BombPowerup, FlamePowerup, SpeedPowerup
    ])(pos=(x, y))
    
    # Recolección
    if player.rect.colliderect(powerup.rect):
        powerup.apply(player)

Notas:
    Los powerups desaparecen automáticamente después de 10 segundos
    si no son recogidos. Los efectos temporales duran 15 segundos.
"""


import pygame
import random
import math
from settings import PowerUpConfig, SnowConfig, WaterConfig, GlobeConfig, CELL_SIZE
from utils import load_image


class PowerUp:
    """
    Power-up que aparece al destruir ladrillos.
    Aplica efectos a Bomberman al recogerlo.
    """

    # Tipos usando configuración de settings.py
    TYPES = {
        'extra_life': {
            'name': 'Vida Extra',
            'color': (255, 50, 50),
            'image': 'heart.png',
        },
        'speed_boost': {
            'name': 'Velocidad',
            'color': (50, 255, 50),
            'image': 'speed.png',
        },
        'bomb_range': {
            'name': 'Rango de Bomba',
            'color': (255, 150, 50),
            'image': 'fire.png',
        },
        'extra_bomb': {
            'name': 'Bomba Extra',
            'color': (150, 50, 255),
            'image': 'bomb_item.png',
        },
        'invincibility': {
            'name': 'Invencibilidad',
            'color': (255, 255, 50),
            'image': 'star.png',
        }
    }

    def __init__(self, pos, powerup_type=None):
        self.x, self.y = pos
        self.width = CELL_SIZE
        self.height = CELL_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.type = powerup_type if powerup_type else self._random_type()
        self.info = self.TYPES[self.type]

        # Imagen desde cache de utils
        self.image = load_image(self.info['image'])

        # Animación flotante
        self.float_offset = 0.0
        self.float_speed = PowerUpConfig.FLOAT_SPEED

        self.collected = False
        self.remove = False

    @classmethod
    def _random_type(cls):
        """Elige tipo aleatorio según probabilidades de settings.py."""
        weighted_types = []
        for ptype, prob in PowerUpConfig.PROBABILITIES.items():
            if ptype in cls.TYPES:
                weight = int(prob * 100)
                weighted_types.extend([ptype] * weight)

        return random.choice(weighted_types) if weighted_types else 'extra_life'

    def apply_effect(self, bomberman):
        """
        Aplica el efecto del power-up a Bomberman.

        Args:
            bomberman: Instancia de Bomberman
        """
        if self.type == 'extra_life':
            bomberman.lives = min(bomberman.lives + 1, bomberman.max_lives)

        elif self.type == 'speed_boost':
            bomberman.speed = min(
                bomberman.speed + PowerUpConfig.SPEED_BOOST_AMOUNT,
                PowerUpConfig.MAX_SPEED
            )

        elif self.type == 'bomb_range':
            if hasattr(bomberman, 'bomb_range'):
                bomberman.bomb_range = min(bomberman.bomb_range + 1, 5)
            else:
                bomberman.bomb_range = 3

        elif self.type == 'extra_bomb':
            if hasattr(bomberman, 'max_bombs'):
                bomberman.max_bombs += 1
            else:
                bomberman.max_bombs = 2

        elif self.type == 'invincibility':
            bomberman.invincibility_timer = PowerUpConfig.INVINCIBILITY_TIME

        self.collected = True
        self.remove = True

    def update(self, dt, bomberman):
        """Actualiza animación y verifica colisión."""
        self.float_offset += self.float_speed * dt * math.pi

        if bomberman.rect.colliderect(self.rect):
            self.apply_effect(bomberman)

    def draw(self, screen, camera):
        """Dibuja el power-up con efecto flotante y soporte de zoom."""
        float_y = math.sin(self.float_offset) * 3
        zoom = getattr(camera, 'zoom', 1.0)

        screen_x, screen_y = camera.apply(self.x, self.y)
        img = self.image
        if zoom != 1.0:
            cs = max(1, int(self.image.get_width() * zoom))
            img = pygame.transform.scale(img, (cs, cs))
        screen.blit(img, (int(screen_x), int(screen_y + float_y * zoom)))


# SNOW TILE

class SnowTile:
    """Bloque de nieve dejado por el enemigo Snow."""

    def __init__(self, pos):
        self.x, self.y = pos
        self.width = CELL_SIZE
        self.height = CELL_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.lifetime = SnowConfig.SNOW_LIFETIME
        self.timer = 0.0
        self.slow_factor = SnowConfig.SNOW_SLOW_FACTOR

        self.alpha = 150
        self.color = (150, 200, 255)
        self.remove = False

    def update(self, dt):
        """Actualiza el timer y alpha."""
        self.timer += dt
        remaining = 1.0 - (self.timer / self.lifetime)
        self.alpha = int(150 * max(0, remaining))

        if self.timer >= self.lifetime:
            self.remove = True

    def draw(self, screen, camera):
        """Dibuja el bloque de nieve con soporte de zoom."""
        zoom = getattr(camera, 'zoom', 1.0)
        cs = max(1, int(self.width * zoom))
        screen_x, screen_y = camera.apply(self.x, self.y)

        snow_surf = pygame.Surface((cs, cs))
        snow_surf.set_alpha(self.alpha)
        snow_surf.fill(self.color)
        screen.blit(snow_surf, (int(screen_x), int(screen_y)))
        pygame.draw.rect(screen, (200, 230, 255),
                         (int(screen_x), int(screen_y), cs, cs), 2)

class WaterPuddle:
    """Charco de agua que hace resbalar al jugador."""
    
    def __init__(self, pos):
        self.x, self.y = pos
        self.width = CELL_SIZE
        self.height = CELL_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.lifetime = WaterConfig.PUDDLE_LIFETIME
        self.timer = 0.0
        self.remove = False
        
        # Visual
        self.alpha = 120
        self.color = (100, 150, 255)  # Azul agua
    
    def update(self, dt):
        """Actualiza el timer del charco."""
        self.timer += dt
        
        # Fade out en últimos segundos
        remaining = 1.0 - (self.timer / self.lifetime)
        self.alpha = int(120 * max(0, remaining))
        
        if self.timer >= self.lifetime:
            self.remove = True
    
    def draw(self, screen, camera):
        """Dibuja el charco con transparencia visible."""
        screen_x, screen_y = camera.apply(self.x, self.y)
        cs = self.width

        # Superficie con SRCALPHA para transparencia correcta
        puddle_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

        # Fondo oscuro azul
        puddle_surf.fill((60, 100, 200, max(40, self.alpha)))

        # Elipse interior más clara para dar profundidad
        inner = pygame.Rect(cs // 6, cs // 4, cs * 2 // 3, cs // 2)
        pygame.draw.ellipse(puddle_surf,
                            (120, 180, 255, min(210, self.alpha + 50)),
                            inner)

        screen.blit(puddle_surf, (int(screen_x), int(screen_y)))

        # Borde sólido sin alpha (siempre visible)
        pygame.draw.rect(screen, (40, 100, 220),
                         (int(screen_x), int(screen_y), cs, cs), 2)

class EnemyPowerup:
    """Powerup que solo afecta a enemigos."""
    
    COLORS = {
        'speed_boost': (255, 200, 0),    # Amarillo
        'health_boost': (255, 50, 50),   # Rojo
        'armor': (150, 150, 255)         # Azul plateado
    }
    
    def __init__(self, pos, powerup_type):
        self.x, self.y = pos
        self.width = 24
        self.height = 24
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.type = powerup_type
        self.color = self.COLORS.get(powerup_type, (255, 255, 255))
        self.collected = False
        
        # Animación flotante
        self.float_offset = 0.0
        self.float_speed = 3.0
    
    def apply_to_enemy(self, enemy):
        """Aplica efecto del powerup y activa aura visual."""
        if self.type == 'speed_boost':
            if not hasattr(enemy, '_base_speed'):
                enemy._base_speed = enemy.speed
            enemy.speed = min(enemy.speed + GlobeConfig.SPEED_BOOST_AMOUNT, 350)
            enemy._speed_boost_timer  = GlobeConfig.SPEED_BOOST_DURATION
            enemy._powerup_aura_timer = GlobeConfig.SPEED_BOOST_DURATION

        elif self.type == 'health_boost':
            enemy.lives = min(enemy.lives + GlobeConfig.HEALTH_BOOST_AMOUNT, 10)
            enemy._powerup_aura_timer = 4.0

        elif self.type == 'armor':
            enemy.invincibility_timer    = GlobeConfig.ARMOR_DURATION
            enemy.invincibility_duration = GlobeConfig.ARMOR_DURATION
            enemy._powerup_aura_timer    = GlobeConfig.ARMOR_DURATION

        enemy.active_powerup = self.type
        self.collected = True
    
    def update(self, dt):
        """Actualiza animación."""
        self.float_offset += self.float_speed * dt * math.pi
    
    def draw(self, screen, camera):
        """Dibuja el powerup."""
        float_y = math.sin(self.float_offset) * 3
        screen_x, screen_y = camera.apply(self.x, self.y)
        
        # Dibujar círculo brillante
        pygame.draw.circle(screen, self.color,
                          (int(screen_x + self.width // 2),
                           int(screen_y + self.height // 2 + float_y)),
                          self.width // 2)
        
        # Borde brillante
        pygame.draw.circle(screen, (255, 255, 255),
                          (int(screen_x + self.width // 2),
                           int(screen_y + self.height // 2 + float_y)),
                          self.width // 2, 2)

# FUNCIÓN HELPER

def try_drop_powerup(pos):
    """
    Intenta generar un power-up al destruir un ladrillo.

    Args:
        pos: Tupla (x, y) donde apareció el ladrillo

    Returns:
        PowerUp o None
    """
    if random.random() < PowerUpConfig.DROP_CHANCE:
        return PowerUp(pos)
    return None

# KEY — Llave para abrir la puerta

class Key:
    """
    Llave coleccionable que dropea un enemigo al morir.
    Cada jugador necesita recoger exactamente una.
    Cuando TODOS los jugadores tienen llave, la puerta se abre.
    """

    def __init__(self, pos):
        self.x, self.y = pos
        self.width  = CELL_SIZE
        self.height = CELL_SIZE
        self.rect   = pygame.Rect(self.x, self.y, self.width, self.height)

        # Intentar cargar sprite; si falla se dibuja con formas
        try:
            self.image = load_image('key.png')
        except Exception:
            self.image = None

        # Animación flotante
        self.float_offset = 0.0
        self.float_speed  = 3.5

        self.collected = False
        self.owner     = None   # jugador que la recogió
        self.remove    = False

    def update(self, dt, players):
        """Detecta colisión con jugadores que aún no tienen llave."""
        self.float_offset += self.float_speed * dt * math.pi

        if self.collected:
            return

        for player in players:
            if player.dead or getattr(player, 'finish', False):
                continue
            if getattr(player, 'has_key', False):
                continue
            if player.rect.colliderect(self.rect):
                self.collected = True
                self.owner     = player
                player.has_key = True
                self.remove    = True
                print(f"{player.label} recogió la llave")
                break

    def draw(self, screen, camera):
        """Dibuja la llave con efecto flotante."""
        if self.collected:
            return

        float_y = math.sin(self.float_offset) * 4
        sx, sy  = camera.apply(self.x, self.y)
        sy     += float_y

        if self.image:
            screen.blit(self.image, (int(sx), int(sy)))
            return

        # ── Fallback visual: rombo dorado + detalle de llave ──
        cx = int(sx + self.width  // 2)
        cy = int(sy + self.height // 2)
        r  = self.width // 2 - 3

        # Sombra
        shadow_pts = [(cx+1, cy-r+1), (cx+r+1, cy+1),
                      (cx+1, cy+r+1), (cx-r+1, cy+1)]
        pygame.draw.polygon(screen, (100, 80, 0), shadow_pts)

        # Cuerpo del rombo (dorado)
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(screen, (255, 215, 0), pts)
        pygame.draw.polygon(screen, (200, 150, 0), pts, 2)

        # Detalle: círculo (cabeza de llave) + línea (tallo)
        pygame.draw.circle(screen, (200, 150, 0), (cx, cy - r // 2), r // 3, 2)
        pygame.draw.line(screen,   (200, 150, 0), (cx, cy - r // 5),
                         (cx, cy + r // 3), 2)
        # Dientes
        pygame.draw.line(screen, (200, 150, 0),
                         (cx, cy + r // 6), (cx + r // 4, cy + r // 6), 2)
        pygame.draw.line(screen, (200, 150, 0),
                         (cx, cy + r // 3), (cx + r // 4, cy + r // 3), 2)


# FROZEN PUDDLE - Charco Congelado (Combo Agua + Nieve)

class FrozenPuddle:
    """
    Charco congelado formado por la mezcla de agua y nieve.
    
    Efectos:
    - Resbalón (como agua)
    - Congelación que persiste después de salir del charco
    """
    
    def __init__(self, pos):
        self.x, self.y = pos
        self.width = CELL_SIZE
        self.height = CELL_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Lifetime heredado del más largo (snow)
        self.lifetime = max(WaterConfig.PUDDLE_LIFETIME, SnowConfig.SNOW_LIFETIME)
        self.timer = 0.0
        self.remove = False
        
        # Visual - Azul cristalino
        self.alpha = 180
        self.base_color = (120, 200, 255)  # Azul claro brillante
        self.ice_color = (200, 240, 255)   # Casi blanco
        
        # Animación de cristales
        self.crystal_timer = 0.0
        self.crystal_speed = 4.0
    
    def update(self, dt):
        """Actualiza el timer y animación."""
        self.timer += dt
        self.crystal_timer += dt * self.crystal_speed
        
        # Fade out en últimos segundos
        remaining = 1.0 - (self.timer / self.lifetime)
        self.alpha = int(180 * max(0, remaining))
        
        if self.timer >= self.lifetime:
            self.remove = True
    
    def draw(self, screen, camera):
        """Dibuja el charco congelado con efecto cristalino."""
        screen_x, screen_y = camera.apply(self.x, self.y)
        cs = self.width
        
        # Superficie con transparencia
        frozen_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
        
        # Capa base - Azul cristalino
        frozen_surf.fill((*self.base_color, max(60, self.alpha)))
        
        # Capa de cristales - Efecto brillante pulsante
        crystal_alpha = int(100 + 60 * abs(math.sin(self.crystal_timer)))
        
        # Cristal central
        center_rect = pygame.Rect(cs // 4, cs // 4, cs // 2, cs // 2)
        pygame.draw.ellipse(frozen_surf, 
                           (*self.ice_color, min(crystal_alpha, self.alpha)),
                           center_rect)
        
        # Destellos en las esquinas (efecto de hielo)
        corners = [
            (cs // 6, cs // 6),
            (cs * 5 // 6, cs // 6),
            (cs // 6, cs * 5 // 6),
            (cs * 5 // 6, cs * 5 // 6)
        ]
        for cx, cy in corners:
            sparkle_alpha = int(crystal_alpha * 0.7)
            pygame.draw.circle(frozen_surf,
                             (*self.ice_color, min(sparkle_alpha, self.alpha)),
                             (cx, cy), cs // 8)
        
        screen.blit(frozen_surf, (int(screen_x), int(screen_y)))
        
        # Borde brillante
        border_color = (180, 230, 255) if self.alpha > 100 else (120, 180, 220)
        pygame.draw.rect(screen, border_color,
                        (int(screen_x), int(screen_y), cs, cs), 2)