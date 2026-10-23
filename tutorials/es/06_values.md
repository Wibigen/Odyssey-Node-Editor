# Variables, valores y matemáticas

## Variables (categoría *Variables*)

| Bloque | Uso |
|---|---|
| **Declare variable** | Una variable local (tipo, nombre, valor inicial opcional). Vive en el flujo donde la declaras. |
| **Set variable** | Asignar un nuevo valor. |
| **Get variable** | Leer el valor actual (una salida de valor, sin pin de ejecución). |
| **Global variable** | Conserva su valor entre fotogramas y llamadas. Un *Declare variable* fuera de una función también se convierte en global. |
| **Constant (value)** | Un número, texto, bool o cualquier valor C++ que escribas. |

Usa **Avanzado** en el inspector para calificadores (`static`, `const`…) y arrays (tamaño y contenido).

> Una variable local declarada dentro de una rama solo existe en esa rama (como en C++).

## Matemáticas y lógica

Dibujados como pequeños cuadrados:

* **Math (A + B)**: `+ - * / %` sobre dos valores (elige el tipo).
* **Compare**: `== != < > <= >=`, da un bool.
* **Logic**: AND / OR; **NOT** invierte un bool.

Conecta el resultado a la condición de un **Branch**, a una variable o a un argumento de una llamada.

## ¿Valor fijo o conexión?

Cualquier pin de entrada puede **conectarse** a un nodo o recibir un **valor fijo** (escríbelo en el inspector). Una entrada conectada oculta su valor fijo.

## Tipos

Los colores de los pines muestran los tipos; el editor no comprueba los tipos de puntero entre conexiones (por ejemplo `StageScene*` hacia `al::LiveActor*` es un error de C++ que verás al compilar). Usa **Cast** (Punteros y memoria) cuando necesites convertir.
