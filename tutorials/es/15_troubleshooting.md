# Solución de problemas

| Problema | Qué probar |
|---|---|
| *El catálogo de funciones está vacío* | Herramientas > Ajustes: elige tu carpeta de OdysseyDecomp (con `data/file_list.yml`) y extrae el catálogo. |
| Una función devuelve `void` pero no debería | Cambia el tipo de retorno (consulta *Llamar y enganchar funciones del juego*). |
| La pestaña *Problemas* muestra algo | Haz doble clic en una línea: se selecciona el nodo. Normalmente una entrada sin conectar o una variable que falta. |
| La compilación no encuentra una cabecera | Añádela en la pestaña **Includes** o corrige las carpetas de inclusión de tu proyecto. |
| La carpeta de compilación está rota | Herramientas > **Reparar la base de exlaunch**. |
| No pasa nada en el juego | ¿Está instalado el hook (símbolo correcto)? ¿Es la carpeta del mod la que carga Ryujinx (pestaña Ryujinx)? ¿Hay otro mod desactivado? |
| El juego se cierra | Un puntero es nulo o un offset es incorrecto. Añade comprobaciones **Is null?**; confirma los offsets para la versión 1.0.0. |
| Un atajo no funciona | Herramientas > Atajos de teclado: puede que se haya cambiado. |
| La disposición de la ventana es rara | Ver: muestra el panel de salida (Ctrl+J); arrastra los paneles a donde quieras. |

Si informas de un problema, incluye el registro de **Build** (Guardar el registro de compilación).
