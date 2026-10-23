# El lienzo: nodos, pines y enlaces

## Nodos y pines

Un nodo tiene **pines de entrada** a la izquierda y **pines de salida** a la derecha.

* Los **pines con flecha blanca** son el **orden de ejecución**: el nodo se ejecuta después del que está conectado a su pin *in* y continúa por *next*.
* Los **círculos de color** son **valores**. El color depende del tipo (número, puntero, bool, texto…). Un círculo lleno está conectado; uno vacío está libre.
* Una entrada sin conectar muestra un **valor fijo** que escribes en el inspector (`= 60`).

## Conectar

* **Arrastra de un pin a otro** (una salida a una entrada).
* Una salida de valor puede alimentar **varias** entradas; una salida de ejecución va a **un solo** nodo siguiente.
* **Suelta en un espacio vacío**: un menú ofrece *Función del juego…*, *Función de plugin…* (cuando un plugin tiene catálogo) y todos los bloques que encajan; el nuevo nodo se crea y se conecta por ti. (Se puede desactivar en Preferencias.)
* Selecciona un nodo y pulsa **Supr** para eliminarlo; *Inspector > Desconectar* quita solo sus enlaces.

## Moverse

| Acción | Cómo |
|---|---|
| Zoom | Rueda del ratón (Ctrl +/-) |
| Desplazar la vista | Mantén el **botón central** y arrastra |
| Encuadrar todo | **F** |
| Seleccionar varios | Arrastra un rectángulo en un espacio vacío; Ctrl+A para todos |
| Duplicar / eliminar | Ctrl+D / Supr |
| Deshacer / rehacer | Ctrl+Z / Ctrl+Y |
| Buscar un nodo | Ctrl+F en el grafo (el icono de búsqueda) |
| Ordenar | Ctrl+L organiza los nodos automáticamente |

## Añadir bloques

* **Haz doble clic** o **arrastra** un bloque desde la lista **Bloques**.
* **Clic derecho** en el lienzo vacío para las mismas opciones, más *Comentar aquí*.
* El cuadro de filtro sobre la lista busca en nombres y descripciones.

## Colores

Cada tipo de nodo tiene su propio color de cabecera. Los nodos que vienen de un **plugin** tienen además un suave resplandor del color del plugin, para distinguirlos de un vistazo.
