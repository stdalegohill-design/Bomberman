"""
Punto de entrada principal del juego Bomberman.

Este módulo sirve como entry point de la aplicación. Su única responsabilidad
es importar y ejecutar la función main() del módulo game.py, que inicializa
y ejecuta el loop principal del juego.

Uso:
    Ejecutar directamente desde la línea de comandos:
        $ python main.py
    
    O como módulo:
        $ python -m main

Notas:
    Este diseño separa el punto de entrada de la lógica principal,
    facilitando testing, empaquetado y distribución del juego.
"""

from game import main

if __name__ == "__main__":
    main()