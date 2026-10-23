# Empieza aquí

**Odyssey Node Editor** te permite crear un mod para **Super Mario Odyssey 1.0.0** sin escribir C++ a mano. Conectas **nodos** en un lienzo y el editor escribe el código de [exlaunch](https://github.com/shadowninja108/exlaunch) por ti. Sigues compilándolo con tu propio proyecto exlaunch.

## La idea en un minuto

1. Un nodo **hook** dice *«cuando el juego ejecute esta función, ejecuta mi grafo»*.
2. Después conectas nodos: llamar a funciones del juego, cambiar variables, comprobar condiciones, hacer bucles.
3. La pestaña **Código C++** muestra el resultado en vivo.
4. **Escribir en el proyecto** coloca el código en tu proyecto exlaunch, **Compilar** lo construye y la pestaña **Ryujinx** inicia el juego con tu mod.

## Lo que necesitas

* Una carpeta con **OdysseyDecomp** (el editor lee su lista de símbolos para conocer cada función del juego).
* Un **proyecto exlaunch** (por ejemplo una copia de SMO-Exlaunch-Base) que puedas compilar.
* *(opcional)* Ryujinx, para probar.

## La ventana

| Zona | Qué es |
|---|---|
| Menús + barra de herramientas | Archivo, Edición, Biblioteca, Ver, Herramientas, Plugins, Ayuda; los iconos más usados |
| **Bloques** (izquierda) | Todos los bloques que puedes añadir, con búsqueda |
| **Lienzo** (centro) | Tu grafo |
| **Inspector** (derecha) | Ajustes del nodo seleccionado |
| **Salida** (abajo) | Código C++, Includes, Problemas, Build, Ryujinx |

Pulsa **Ayuda > Recorrido por la interfaz** para una presentación guiada y sigue después los tutoriales en orden:

1. *Configura tu proyecto*
2. *Tu primer mod*
3. *El lienzo*, y luego los temas que necesites.

**Conviene saber:** el editor nunca compila por sí mismo para la Switch ni toca tus archivos del juego: escribe C++ en el proyecto que le indiques.
