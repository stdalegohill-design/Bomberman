# Educational Project: Custom Grid-Based Action Engine
**Languages:** [English](#english) | [Español](#español) | [Deutsch](#deutsch)

---

<a name="english"></a>
## English: Project Philosophy and Technical Architecture

### Development Approach: Engine-less Mastery
This project is a technical implementation of a grid-based action game, developed strictly for educational purposes. Unlike modern commercial projects, this software was built **without a pre-existing game engine** (such as Godot or Unity). The decision to construct a custom engine using Python was a deliberate choice to master low-level game development mechanics, including:

* **Manual Game Loop:** Implementation of the Event Handling → Logic Update → Rendering pipeline.
* **Mathematical Viewports:** Calculation of camera matrices and dynamic split-screen coordinate systems using trigonometric and linear logic.
* **Custom Physics & Collisions:** Physics logic built from the ground up using the **Python Standard Library** (`math` for vector distance and `random` for procedurality) instead of specialized external physics engines.

### Technical Stack & Dependencies
The project relies on a minimal set of tools to emphasize programmatic logic:
* **Pygame:** Used as a multimedia interface for drawing surfaces and handling raw input.
* **Standard Library:** Extensive use of `math` (geometry/collisions), `random` (procedural generation), `heapq` (optimized A* priority queues), and `os/sys` (resource management).

### Architecture & Design Patterns
* **Hierarchical Entity System (`entities.py`):** A multi-level inheritance tree (`AnimatedEntity` → `MovableEntity` → `PathfindingEntity` → `LivingEntity`) to minimize code redundancy.
* **Finite State Machine (FSM) (`states.py`):** Management of game flow through the State Pattern, isolating logic for menus, gameplay, and transitions.
* **Procedural Generation & IA:** **DFS (Depth-First Search)** for maze generation and **A* (A-Star)** for intelligent agent navigation.

### Technological Evolution
1. **PGZero:** Prototyping phase.
2. **Pygame (Current):** Migration for direct `Surface` control and complex rendering.
3. **Arcade (Proposed):** Future migration for OpenGL hardware acceleration.
   
*Future projects will transition to Godot/Unity to leverage professional workflow tools.*

---

<a name="español"></a>
## Español: Filosofía de Desarrollo y Arquitectura Técnica

### Enfoque de Desarrollo: Dominio de Bajo Nivel
Este proyecto es una implementación técnica de un juego de acción basado en cuadrículas, desarrollado estrictamente con fines educativos. A diferencia de los proyectos comerciales modernos, este software se construyó **sin un motor de videojuegos preexistente** (como Godot o Unity). La decisión de crear un motor personalizado utilizando Python fue una elección deliberada para dominar las mecánicas de bajo nivel, incluyendo:

* **Game Loop Manual:** Implementación del pipeline Manejo de Eventos → Actualización de Lógica → Renderizado.
* **Viewports Matemáticos:** Cálculo de matrices de cámara y sistemas de coordenadas para pantalla dividida dinámica mediante lógica lineal.
* **Resolución de Colisiones Personalizada:** Construcción de la lógica física desde cero utilizando la **Librería Estándar de Python** (especialmente `math` para cálculos vectoriales y `random` para variabilidad) en lugar de motores de física externos.

### Stack Tecnológico y Dependencias
El proyecto se apoya en un conjunto mínimo de herramientas para enfatizar la lógica de programación:
* **Pygame:** Utilizado como interfaz multimedia para el renderizado de superficies y manejo de inputs.
* **Librería Estándar:** Uso intensivo de `math` (geometría), `random` (generación procedimental), `heapq` (colas de prioridad para A*) y `os/sys` (gestión de recursos).

### Arquitectura y Patrones de Diseño
* **Sistema Jerárquico de Entidades (`entities.py`):** Árbol de herencia multinivel (`AnimatedEntity` → `MovableEntity` → `PathfindingEntity` → `LivingEntity`) para garantizar un comportamiento consistente.
* **Máquina de Estados Finitos (FSM) (`states.py`):** Gestión del flujo mediante el Patrón de Estado, aislando la lógica de menús y gameplay.
* **IA y Generación Procedimental:** Algoritmos de **Búsqueda en Profundidad (DFS)** para laberintos y **A* (A-Estrella)** para la navegación inteligente de enemigos.

### Evolución Tecnológica
1. **PGZero:** Fase de prototipado.
2. **Pygame (Actual):** Migración para control total del pipeline de renderizado.
3. **Arcade (Propuesta):** Evaluación de migración para aprovechar aceleración por GPU.
   
*Proyectos futuros utilizarán Godot o Unity para aprovechar herramientas de flujo de trabajo profesional.*

---

<a name="deutsch"></a>
## Deutsch: Entwicklungsphilosophie und Technische Architektur

### Entwicklungsansatz: Low-Level-Beherrschung
Dieses Projekt ist eine technische Implementierung eines rasterbasierten Action-Spiels. Im Gegensatz zu kommerziellen Projekten wurde diese Software **ohne eine vorhandene Game-Engine** entwickelt. Die Entscheidung, eine eigene Engine mit Python zu erstellen, war eine bewusste Wahl, um die Grundlagen zu meistern:

* **Manueller Game Loop:** Ereignisbehandlung → Logik-Update → Rendering.
* **Kameramatrizen:** Mathematische Berechnung von Viewports für dynamischen Split-Screen.
* **Eigene Physik-Logik:** Entwicklung der Kollisionsabfrage von Grund auf unter Verwendung der **Python-Standardbibliothek** (`math` und `random`) anstelle externer Physik-Engines.

### Technologie-Stack
* **Pygame:** Multimedia-Schnittstelle für Rendering und Input.
* **Standardbibliothek:** Einsatz von `math` (Geometrie), `random` (Prozedurale Generierung), `heapq` (A*-Algorithmus) und `os`.


### Architektur
* **Entitätssystem:** Mehrstufige Vererbung zur Reduzierung von redundantem Code.
* **Zustandsautomat (FSM):** Saubere Trennung von Menü- und Spiellogik durch das State-Pattern.
* **KI & Algorithmen:** Einsatz von **Tiefensuche (DFS)** für Labyrinthe und **A*-Pfadfindung** für intelligente Gegner.

### Technologische Evolution
1. **PGZero:** Prototyping.
2. **Pygame (Aktuell):** Migration zur direkten Kontrolle der Rendering-Pipeline.
3. **Arcade (Geplant):** Zukünftige Migration zur Nutzung von OpenGL.
   
*Zukünftige Projekte werden auf Godot oder Unity setzen, um professionelle Tools zu nutzen.*
