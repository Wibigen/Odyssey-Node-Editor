# Llamar y enganchar funciones del juego

Haz clic en **Función del juego…** (Ctrl+Mayús+F) para buscar en el catálogo de funciones de Super Mario Odyssey.

## El explorador

* Escribe parte de un nombre, clase o descripción. Las categorías de la izquierda reducen la lista.
* Selecciona una función para ver su **firma, tipo de retorno, offset y símbolo**.
* La estrella ☆ marca los **favoritos**; **Abrir en GitHub** abre una búsqueda en OdysseyDecomp (útil para leer lo que hace realmente).

## ¿Llamar o enganchar?

| | **Llamar a esta función desde mi mod** | **Enganchar esta función** |
|---|---|---|
| Significado | *Mi grafo llama a esta función del juego* | *Cuando el juego la llama, se ejecuta mi grafo* |
| Nodo | Un nodo dentro de tu flujo | Un nodo de entrada rojo (sin entrada) |
| Uso típico | `al::setPos(actor, …)`, `kill`, leer un valor | Ejecutar tu código en cada fotograma, al recibir un golpe, al recoger algo |

### Argumentos de una llamada

Cada argumento es **Conectar un nodo** (conectar un valor) o un **Valor fijo**: un número, texto, bool, un `Vector3` (campos X/Y/Z) o cualquier expresión C++.

### Resultado

Una llamada que devuelve un valor puede **guardarlo en una variable** (ponle nombre en el inspector) o usarse **directamente como valor** dentro de otro nodo (*Usar como valor* en el inspector o en el menú contextual).

## Modos del hook

| Modo | Qué se ejecuta |
|---|---|
| **Ejecutar primero el original y luego mi grafo** | La función del juego y después tu lógica (por defecto). |
| **Ejecutar primero mi grafo y luego el original** | Tu lógica y después la del juego. |
| **Reemplazar el original** | Solo tu grafo. |
| **Manual** | Colocas nodos **Call original (Orig)** donde quieras dentro de tu grafo. |

En modo *antes* con valor de retorno, una salida **original result** te da lo que devolvió el juego. Cambia el tipo de retorno o los nombres de los argumentos en el inspector si hace falta.

## ¿Tipo de retorno incorrecto?

El catálogo deduce los tipos de retorno a partir de las cabeceras. Si una función dice `void` pero devuelve algo, usa **Cambiar…** junto al tipo de retorno (una advertencia pide confirmación). La elección se recuerda.

## Llamada por nombre

Para lo que no está en el catálogo, usa **Call by name** (Funciones): cualquier función C++ escrita por su nombre, p. ej. `sead::Mathf::sqrt(x)`. **Get scene object** cubre `al::getSceneObj<T>(…)`.

## Estilo de llamada

*Preferencias > Avanzado*: las llamadas son C++ normal por defecto (`rs::getPlayerActor(scene)`), o por dirección. Un nodo concreto puede cambiarlo (*Estilo de llamada* en el inspector). Los hooks se instalan **por símbolo** por defecto; la forma por offset es la alternativa.
