# Ihr Projekt einrichten

Öffnen Sie **Werkzeuge > Einstellungen** (Strg+Umschalt+,). Beim ersten Mal öffnet sich das Fenster von selbst.

## 1. Der OdysseyDecomp-Ordner

Wählen Sie den Ordner Ihrer [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp)-Kopie (den mit `data/file_list.yml`). Der Editor erstellt daraus den **Funktionskatalog** (etwa 17.700 Funktionen): Namen, Argumente, Rückgabetypen, Offsets und Symbole. Das geschieht einmal und wird gespeichert. Zum Lesen der gemangelten Namen wird das Werkzeug `c++filt` benötigt; es wird automatisch gefunden, oder Sie geben es im selben Fenster an.

Wenn der Katalog für eine Funktion `void` angibt, die in Wirklichkeit etwas zurückgibt, können Sie das später korrigieren (siehe *Spielfunktionen aufrufen und hooken*).

## 2. Ihr exlaunch-Projekt

* **Projektordner**: das Stammverzeichnis Ihres exlaunch-Projekts (das mit `CMakeLists.txt`). Windows-Pfade, `\\wsl$\Ubuntu\home\me\proj` und WSL-Pfade werden verstanden.
* **Erzeugte Datei**: wohin der Code geschrieben wird. Leer = `src/program/main.cpp` oder `src/main.cpp`, je nachdem, welche existiert.

## 3. Der Build-Befehl

Standard: `cmake --build build`. Wählen Sie, wo er läuft: **Windows (cmd)**, **WSL** (Distribution wählen, zum Beispiel Ubuntu) oder die native Shell. Beim ersten *Kompilieren* wird gefragt, falls nichts eingestellt ist.

## 4. Testen

Öffnen Sie den Reiter **Ryujinx** (unten) und legen Sie einmalig die Ryujinx-Programmdatei, die Spieldatei und einen Mod-Namen fest. *Mod installieren und starten* kopiert Ihren Build in den Mod-Ordner von Ryujinx und startet das Spiel.

## Wenn etwas nicht gefunden wird

* Reiter **Probleme**: was der Graph noch braucht.
* **Werkzeuge > exlaunch-Basis reparieren**: löscht den Ordner `build` und führt CMake erneut aus (behebt ein defektes Setup).
* Die Einstellungen können jederzeit wieder geöffnet werden; nichts geht verloren.
