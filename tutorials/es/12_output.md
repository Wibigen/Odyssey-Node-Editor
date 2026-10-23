# Código, problemas y compilación

El panel **Salida** de abajo tiene cinco pestañas. Contráelo con la flecha, **Ctrl+J** o un doble clic en una pestaña.

## Código C++

Vista previa en vivo del archivo generado. Las líneas del **nodo seleccionado** aparecen resaltadas. **Copiar** y **Guardar como…** lo exportan.

## Includes

Las cabeceras al principio del archivo (consulta *Código personalizado*).

## Problemas

Lo que falta o está mal **antes** de compilar: entradas sin conectar, variables desconocidas, hooks vacíos. Haz doble clic en una línea para ir al nodo.

## Build

* **Escribir en el proyecto** (Ctrl+E) guarda el código en tu proyecto exlaunch.
* **Compilar** (F5) ejecuta el comando de compilación y muestra la salida. **Copiar errores** copia solo las líneas de error; **Guardar el registro de compilación** conserva toda la consola.
* **Reparar base** (menú Herramientas) elimina `build/` y vuelve a ejecutar CMake.

## Ryujinx

Indica una vez el emulador, el archivo del juego y un nombre de mod. **Instalar el mod y lanzar** copia `subsdkN` y `main.npdm` de tu carpeta de compilación a la carpeta de mods de Ryujinx e inicia el juego. Las opciones incluyen compilar primero, desactivar otros mods y pantalla completa.

## Importante

El editor en sí nunca compila para la Switch: lo hace la cadena de herramientas de tu proyecto. Si una compilación falla, copia el registro (indica exactamente qué archivo y qué línea).
