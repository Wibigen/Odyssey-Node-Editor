# Tu primer mod

Objetivo: ejecutar algo **una vez por segundo** durante el juego. El grafo de ejemplo lo hace; aquí lo construyes tú mismo para conocer cada parte.

## 1. Enganchar una función del juego

1. Haz clic en **Función del juego…** (botón rojo, o Ctrl+Mayús+F).
2. Busca `exePlay` y selecciona **StageScene::exePlay** (se ejecuta en cada fotograma mientras juegas).
3. Elige **Enganchar esta función**, deja el modo *Ejecutar primero el original y luego mi grafo* y pulsa **Añadir al grafo**.

Aparece un nodo rojo **Hook StageScene::exePlay**. Su pin blanco **next** es donde empieza tu lógica.

## 2. Contar fotogramas

1. Añade una **Variable global** (Variables): tipo `int`, nombre `frames`, valor inicial `0`. Una variable global conserva su valor de un fotograma al siguiente.
2. Añade **Set variable**, elige `frames` y conecta **hook next → in**.
3. Añade **Get variable** `frames` y **Math (A + B)** de tipo `int`, B = `1`; conecta *Get → A*, *Math out → Set v*.

## 3. Hacer algo cada 60 fotogramas

1. Añade **Branch (if / else)** después del Set variable.
2. Condición: **Compare** `(frames % 60) == 0` (un nodo *Math* con `%` y 60 que alimenta un *Compare* con `== 0`). Conecta el resultado al pin **c** del Branch.
3. Pon lo que quieras en el camino **then**, por ejemplo una **Custom statement** `/* mi código aquí */`, o una llamada a una función del juego.

## 4. Mirar el código

Abre la pestaña **Código C++**: el hook, la variable y el `if` están ahí. Selecciona un nodo: sus líneas se resaltan.

## 5. Compilar y probar

1. ¿La pestaña **Problemas** está vacía? Bien.
2. **Escribir en el proyecto** (Ctrl+E) y luego **Compilar** (F5).
3. Pestaña **Ryujinx** > *Instalar el mod y lanzar*.

> Inicio más rápido: **Archivo > Nuevo desde plantilla** (o el grafo de ejemplo en Preferencias > Abrir con) te da un grafo listo.
