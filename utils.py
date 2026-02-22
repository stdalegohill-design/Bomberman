"""
UTILS.PY - Utilidades y Funciones Compartidas
==============================================

Contiene funciones helper que se usan en múltiples partes del código.
Reduce duplicación y facilita mantenimiento.
"""

import pygame
import os
import math
from settings import IMAGES_DIR, SOUNDS_DIR, Colors

# CARGA DE RECURSOS

_image_cache = {}  # Cache de imágenes cargadas

def load_image(filename, colorkey=None, scale=None):
    """
    Carga una imagen con cache automático.
    
    Args:
        filename: Nombre del archivo (ej: 'player.png')
        colorkey: Color transparente opcional (-1 para usar topleft pixel)
        scale: Tupla (width, height) para escalar la imagen
    
    Returns:
        Surface de pygame con la imagen cargada
    """
    # Verificar cache
    cache_key = (filename, colorkey, scale)
    if cache_key in _image_cache:
        return _image_cache[cache_key]
    
    try:
        path = os.path.join(IMAGES_DIR, filename)
        image = pygame.image.load(path).convert_alpha()
        
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        
        if scale is not None:
            image = pygame.transform.scale(image, scale)
        
        # Guardar en cache
        _image_cache[cache_key] = image
        return image
        
    except pygame.error as e:
        print(f"Error cargando {filename}: {e}")
        # Imagen de placeholder
        surf = pygame.Surface((32, 32))
        surf.fill((255, 0, 255))  # Magenta
        return surf


def load_sound(filename):
    """
    Carga un efecto de sonido.
    
    Args:
        filename: Nombre del archivo de sonido
    
    Returns:
        pygame.mixer.Sound o None si falla
    """
    try:
        path = os.path.join(SOUNDS_DIR, filename)
        return pygame.mixer.Sound(path)
    except (pygame.error, FileNotFoundError) as e:
        print(f"Error cargando sonido {filename}: {e}")
        return None


def apply_tint(surface, tint_color):
    """
    Aplica un tinte de color a una superficie (palette swap programático).
    Los píxeles oscuros absorben poco tinte; los claros absorben más.
    Usa BLEND_MULT: multiplica cada canal RGB del sprite por el tinte / 255.

    Args:
        surface:    pygame.Surface original (con alpha)
        tint_color: Tupla RGB (r, g, b) o None para sin tinte

    Returns:
        Nueva Surface con el tinte aplicado (el original no se modifica)
    """
    if tint_color is None:
        return surface

    tinted = surface.copy()
    # Crear superficie sólida del color deseado y mezclarla con BLEND_MULT
    color_surf = pygame.Surface(tinted.get_size()).convert_alpha()
    color_surf.fill(tint_color)
    tinted.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return tinted


def clear_image_cache():
    """Limpia el cache de imágenes (útil para hot-reload)."""
    global _image_cache
    _image_cache.clear()


# MATEMÁTICAS Y GEOMETRÍA

def distance(pos1, pos2):
    """
    Calcula la distancia euclidiana entre dos puntos.
    
    Args:
        pos1: Tupla (x, y)
        pos2: Tupla (x, y)
    
    Returns:
        float: Distancia entre los puntos
    """
    return math.hypot(pos2[0] - pos1[0], pos2[1] - pos1[1])


def manhattan_distance(pos1, pos2):
    """
    Calcula la distancia Manhattan (|dx| + |dy|).
    
    Args:
        pos1: Tupla (x, y)
        pos2: Tupla (x, y)
    
    Returns:
        float: Distancia Manhattan
    """
    return abs(pos2[0] - pos1[0]) + abs(pos2[1] - pos1[1])


def normalize_vector(vector):
    """
    Normaliza un vector a longitud 1.
    
    Args:
        vector: Tupla (x, y)
    
    Returns:
        Tupla (x, y) normalizada
    """
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2)
    if magnitude == 0:
        return (0, 0)
    return (vector[0] / magnitude, vector[1] / magnitude)


def clamp(value, min_value, max_value):
    """
    Restringe un valor entre un mínimo y máximo.
    
    Args:
        value: Valor a restringir
        min_value: Valor mínimo
        max_value: Valor máximo
    
    Returns:
        Valor restringido
    """
    return max(min_value, min(value, max_value))


def lerp(start, end, t):
    """
    Interpolación lineal entre dos valores.
    
    Args:
        start: Valor inicial
        end: Valor final
        t: Factor de interpolación (0.0 a 1.0)
    
    Returns:
        Valor interpolado
    """
    return start + (end - start) * clamp(t, 0.0, 1.0)


def pixel_to_grid(x, y, cell_size=32):
    """
    Convierte coordenadas de píxeles a coordenadas de grid.
    
    Args:
        x, y: Coordenadas en píxeles
        cell_size: Tamaño de celda
    
    Returns:
        Tupla (row, col) en el grid
    """
    return (int(y // cell_size), int(x // cell_size))


def grid_to_pixel(row, col, cell_size=32, center=False):
    """
    Convierte coordenadas de grid a píxeles.
    
    Args:
        row, col: Coordenadas en el grid
        cell_size: Tamaño de celda
        center: Si True, retorna el centro de la celda
    
    Returns:
        Tupla (x, y) en píxeles
    """
    x = col * cell_size
    y = row * cell_size
    
    if center:
        x += cell_size // 2
        y += cell_size // 2
    
    return (x, y)


# COLISIONES Y FÍSICA

def rects_collide(rect1, rect2):
    """
    Verifica si dos rectángulos colisionan.
    
    Args:
        rect1, rect2: pygame.Rect
    
    Returns:
        bool: True si colisionan
    """
    return rect1.colliderect(rect2)


def point_in_rect(point, rect):
    """
    Verifica si un punto está dentro de un rectángulo.
    
    Args:
        point: Tupla (x, y)
        rect: pygame.Rect
    
    Returns:
        bool: True si el punto está dentro
    """
    return rect.collidepoint(point)


def circle_collision(pos1, radius1, pos2, radius2):
    """
    Verifica colisión entre dos círculos.
    
    Args:
        pos1, pos2: Tuplas (x, y)
        radius1, radius2: Radios de los círculos
    
    Returns:
        bool: True si colisionan
    """
    return distance(pos1, pos2) < (radius1 + radius2)


# TEXTO Y UI

def draw_text(surface, text, pos, font, color=Colors.WHITE, 
              align='left', shadow=False):
    """
    Dibuja texto en pantalla con opciones avanzadas.
    
    Args:
        surface: Superficie donde dibujar
        text: Texto a dibujar
        pos: Tupla (x, y)
        font: pygame.font.Font
        color: Color del texto
        align: 'left', 'center', 'right'
        shadow: Si True, dibuja sombra
    """
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect()
    
    # Alineación
    if align == 'center':
        text_rect.center = pos
    elif align == 'right':
        text_rect.right = pos[0]
        text_rect.y = pos[1]
    else:  # left
        text_rect.topleft = pos
    
    # Sombra
    if shadow:
        shadow_surface = font.render(str(text), True, Colors.BLACK)
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.topleft = (text_rect.x + 2, text_rect.y + 2)
        surface.blit(shadow_surface, shadow_rect)
    
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_text_multiline(surface, text, pos, font, color=Colors.WHITE, 
                        line_spacing=5):
    """
    Dibuja texto multilínea.
    
    Args:
        surface: Superficie donde dibujar
        text: Texto con saltos de línea (\n)
        pos: Tupla (x, y)
        font: pygame.font.Font
        color: Color del texto
        line_spacing: Espaciado entre líneas
    """
    lines = text.split('\n')
    y_offset = 0
    
    for line in lines:
        draw_text(surface, line, (pos[0], pos[1] + y_offset), 
                 font, color, align='left')
        y_offset += font.get_height() + line_spacing


def draw_health_bar(surface, pos, current, maximum, width=100, height=10, 
                    bg_color=Colors.HEALTH_BG, fill_color=Colors.HEALTH_RED):
    """
    Dibuja una barra de vida.
    
    Args:
        surface: Superficie donde dibujar
        pos: Tupla (x, y)
        current: Vida actual
        maximum: Vida máxima
        width, height: Dimensiones de la barra
        bg_color: Color de fondo
        fill_color: Color de relleno
    """
    # Fondo
    bg_rect = pygame.Rect(pos[0], pos[1], width, height)
    pygame.draw.rect(surface, bg_color, bg_rect)
    
    # Relleno
    if current > 0:
        fill_width = int((current / maximum) * width)
        fill_rect = pygame.Rect(pos[0], pos[1], fill_width, height)
        pygame.draw.rect(surface, fill_color, fill_rect)
    
    # Borde
    pygame.draw.rect(surface, Colors.WHITE, bg_rect, 2)


# EFECTOS VISUALES

def draw_particle(surface, pos, radius, color, alpha=255):
    """
    Dibuja una partícula circular con alpha.
    
    Args:
        surface: Superficie donde dibujar
        pos: Tupla (x, y)
        radius: Radio de la partícula
        color: Color RGB
        alpha: Transparencia (0-255)
    """
    if alpha < 255:
        particle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*color, alpha), 
                          (radius, radius), radius)
        surface.blit(particle_surf, (pos[0] - radius, pos[1] - radius))
    else:
        pygame.draw.circle(surface, color, pos, radius)


def draw_flash(surface, alpha=128):
    """
    Dibuja un flash blanco en toda la pantalla.
    
    Args:
        surface: Superficie donde dibujar
        alpha: Intensidad del flash (0-255)
    """
    flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    flash_surf.fill((255, 255, 255, alpha))
    surface.blit(flash_surf, (0, 0))


def draw_screen_shake_offset():
    """
    Genera offset aleatorio para efecto de screen shake.
    
    Returns:
        Tupla (offset_x, offset_y)
    """
    import random
    return (random.randint(-5, 5), random.randint(-5, 5))


# UTILIDADES DE ANIMACIÓN

class Timer:
    """Timer simple para manejar cooldowns y duraciones."""
    
    def __init__(self, duration, autostart=False):
        self.duration = duration
        self.time = 0.0 if autostart else duration
        self.active = autostart
    
    def update(self, dt):
        """Actualiza el timer."""
        if self.active:
            self.time += dt
            if self.time >= self.duration:
                self.active = False
                return True  # Timer completado
        return False
    
    def start(self):
        """Inicia el timer."""
        self.time = 0.0
        self.active = True
    
    def reset(self):
        """Reinicia el timer."""
        self.time = 0.0
        self.active = False
    
    @property
    def progress(self):
        """Retorna el progreso (0.0 a 1.0)."""
        if self.duration == 0:
            return 1.0
        return clamp(self.time / self.duration, 0.0, 1.0)
    
    @property
    def is_finished(self):
        """Retorna True si el timer terminó."""
        return not self.active and self.time >= self.duration


# DEBUG

def draw_debug_rect(surface, rect, color=Colors.DEBUG_HITBOX, width=2):
    """
    Dibuja un rectángulo de debug.
    
    Args:
        surface: Superficie donde dibujar
        rect: pygame.Rect
        color: Color del rectángulo
        width: Grosor de la línea
    """
    pygame.draw.rect(surface, color, rect, width)


def draw_debug_point(surface, pos, color=Colors.DEBUG_PATH, radius=3):
    """
    Dibuja un punto de debug.
    
    Args:
        surface: Superficie donde dibujar
        pos: Tupla (x, y)
        color: Color del punto
        radius: Radio del punto
    """
    pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), radius)


def draw_debug_line(surface, start, end, color=Colors.DEBUG_PATH, width=2):
    """
    Dibuja una línea de debug.
    
    Args:
        surface: Superficie donde dibujar
        start, end: Tuplas (x, y)
        color: Color de la línea
        width: Grosor de la línea
    """
    pygame.draw.line(surface, color, start, end, width)


def print_debug(message, category="DEBUG"):
    """
    Imprime mensaje de debug con formato.
    
    Args:
        message: Mensaje a imprimir
        category: Categoría del mensaje
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{category}] {message}")


# VALIDACIÓN

def validate_position(x, y, map_width, map_height, margin=0):
    """
    Valida que una posición esté dentro de los límites del mapa.
    
    Args:
        x, y: Coordenadas a validar
        map_width, map_height: Dimensiones del mapa
        margin: Margen desde los bordes
    
    Returns:
        bool: True si la posición es válida
    """
    return (margin <= x < map_width - margin and 
            margin <= y < map_height - margin)


# AUTO-EJECUCIÓN (para testing)
if __name__ == "__main__":
    print("UTILS.PY - Test de funciones")
    print("=" * 50)
    
    # Test de distancia
    p1 = (0, 0)
    p2 = (3, 4)
    print(f"Distancia euclidiana: {distance(p1, p2)}")  # Debería ser 5.0
    print(f"Distancia Manhattan: {manhattan_distance(p1, p2)}")  # Debería ser 7
    
    # Test de conversión pixel/grid
    print(f"Pixel (96, 64) -> Grid: {pixel_to_grid(96, 64)}")  # (2, 3)
    print(f"Grid (2, 3) -> Pixel: {grid_to_pixel(2, 3)}")  # (96, 64)
    
    # Test de timer
    timer = Timer(1.0, autostart=True)
    print(f"Timer iniciado, progreso: {timer.progress}")
    
    print("=" * 50)
    print("Tests completados")