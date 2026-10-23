# Control de flujo

Los bloques **Flow** deciden *qué* nodos se ejecutan y *cuántas veces*.

| Bloque | Qué hace |
|---|---|
| **Branch (if / else)** | Condición **c**: ejecuta el camino **then** o el camino **else** y continúa. |
| **Switch** | Elige un camino a partir de un valor entero; edita los casos como pequeñas cajas con el botón **+**. |
| **For loop** | Repite un camino N veces; el índice es una salida. |
| **While loop** | Repite mientras una condición sea verdadera. |
| **Return** | Sale de la función o del hook actual, opcionalmente con un valor. |

## Leer el flujo

Sigue las flechas blancas. Un nodo con dos salidas de flecha (Branch) tiene dos continuaciones posibles; ambas pueden seguir después hacia un nodo común.

## Consejos

* Mantén los bucles cortos: los hooks se ejecutan en el hilo principal del juego, en cada fotograma.
* Para hacer algo **una sola vez** cada vez que cambia una condición, guarda el estado anterior en una **Variable global**.
* Agrupa una idea repetida en tu propia función (siguiente tutorial).
