# Configura tu proyecto

Abre **Herramientas > Ajustes** (Ctrl+Mayús+,). Se abre solo la primera vez.

## 1. La carpeta de OdysseyDecomp

Elige la carpeta de tu copia de [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) (la que contiene `data/file_list.yml`). El editor construye entonces el **catálogo de funciones** (unas 17 700 funciones): nombres, argumentos, tipos de retorno, offsets y símbolos. Se hace una vez y se guarda. Necesita la herramienta `c++filt` para leer los nombres decorados; se encuentra automáticamente, o la indicas en la misma ventana.

Si el catálogo dice `void` para una función que en realidad devuelve algo, puedes corregirlo más tarde (consulta *Llamar y enganchar funciones del juego*).

## 2. Tu proyecto exlaunch

* **Carpeta del proyecto**: la raíz de tu proyecto exlaunch (la que tiene `CMakeLists.txt`). Se entienden las rutas de Windows, `\\wsl$\Ubuntu\home\me\proj` y las rutas WSL.
* **Archivo generado**: dónde se escribe el código. Vacío = `src/program/main.cpp` o `src/main.cpp`, el que exista.

## 3. El comando de compilación

Por defecto: `cmake --build build`. Elige dónde se ejecuta: **Windows (cmd)**, **WSL** (elige la distribución, por ejemplo Ubuntu) o la shell nativa. El primer *Compilar* lo pregunta si no está configurado.

## 4. Pruébalo

Abre la pestaña **Ryujinx** (abajo) e indica una sola vez el ejecutable de Ryujinx, el archivo del juego y un nombre de mod. *Instalar el mod y lanzar* copia tu compilación a la carpeta de mods de Ryujinx e inicia el juego.

## Si algo no se encuentra

* Pestaña **Problemas**: lo que aún necesita el grafo.
* **Herramientas > Reparar la base de exlaunch**: elimina la carpeta `build` y vuelve a ejecutar CMake (arregla una configuración rota).
* Los Ajustes se pueden reabrir en cualquier momento; no se pierde nada.
