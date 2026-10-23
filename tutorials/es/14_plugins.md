# Plugins

Los plugins añaden **nodos**, **catálogos de funciones**, **temas**, **plantillas** y **tutoriales**.

## Explorador de plugins

**Plugins > Explorador de plugins** (Ctrl+Mayús+P): cada plugin con su imagen, autor, versión y contenido. **Activar / Desactivar**, **Instalar…** (un `.zip` / `.odnp` o una carpeta), **Eliminar**, **Nuevo plugin…** (un esqueleto para editar), **Mostrar carpeta**.

Incluidos: *E/S estándar*, *Cadenas*, *Temas adicionales* y **Dear ImGui** (desactivado por defecto).

## Usar lo que añade un plugin

* Los nodos aparecen en la lista **Bloques** bajo las categorías del plugin, con un suave resplandor de color en el lienzo.
* Un catálogo se abre con **Función de plugin…** (Ctrl+Mayús+K, el botón sobre la lista de bloques o el menú al soltar un enlace).
* Plantillas: **Archivo > Nuevo desde plantilla**.
* Tutoriales: ventana **Tutoriales**, sección *Tutoriales de plugins*.

## Plugins que cambian tu proyecto

Algunos plugins (Dear ImGui) necesitan archivos y líneas de CMake en tu proyecto exlaunch. El editor te lo **ofrece** al activarlos: no se sobrescribe nada, se conserva una copia de seguridad de `CMakeLists.txt` y *Explorador de plugins > Base de exlaunch…* quita exactamente lo que se añadió.

## Seguridad

Un plugin con un archivo `plugin.py` ejecuta Python con los mismos permisos que el editor. Instala solo plugins de personas de confianza.

## Escribir uno

Consulta `PLUGINS.md` (formato, plantillas de nodos, temas, páginas de ayuda, ajustes).
