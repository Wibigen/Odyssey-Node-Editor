# Código personalizado e importación de C++

Los nodos cubren mucho, pero no todo. Dos salidas de emergencia te mantienen en marcha.

## Bloques personalizados

* **Custom expression**: cualquier expresión C++ usada como valor.
* **Custom statement**: cualquier sentencia C++ en el flujo.

Conecta hasta ocho entradas y refiérete a ellas como `$a` … `$h` en tu texto:

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## Archivos de inclusión

La pestaña **Includes** (abajo) lista las líneas `#include` del archivo generado. Añade las cabeceras que necesite tu código personalizado.

## Importar C++

**Archivo > Importar archivo C++…** (Ctrl+I) convierte un `.cpp` en un grafo hasta donde lo entiende. Lee el código que escribe esta herramienta y patrones habituales escritos a mano; las plantillas (templates), clases y macros poco comunes se conservan como código personalizado. Revisa después la pestaña *Problemas*.
