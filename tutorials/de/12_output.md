# Code, Probleme und Build

Der Bereich **Ausgabe** unten hat fünf Reiter. Klappen Sie ihn mit dem Pfeil, **Strg+J** oder einem Doppelklick auf einen Reiter ein.

## C++-Code

Live-Vorschau der erzeugten Datei. Die Zeilen des **ausgewählten Knotens** sind hervorgehoben. **Kopieren** und **Speichern unter…** exportieren sie.

## Includes

Die Header am Anfang der Datei (siehe *Eigener Code*).

## Probleme

Was **vor** dem Kompilieren fehlt oder falsch ist: nicht verbundene Eingänge, unbekannte Variablen, leere Hooks. Doppelklicken Sie auf eine Zeile, um zum Knoten zu springen.

## Build

* **Ins Projekt schreiben** (Strg+E) speichert den Code in Ihrem exlaunch-Projekt.
* **Kompilieren** (F5) führt den Build-Befehl aus und zeigt die Ausgabe. **Fehler kopieren** kopiert nur die Fehlerzeilen; **Build-Protokoll speichern** behält die ganze Konsole.
* **Basis reparieren** (Menü Werkzeuge) löscht `build/` und führt CMake erneut aus.

## Ryujinx

Legen Sie Emulator, Spieldatei und Mod-Namen einmalig fest. **Mod installieren und starten** kopiert `subsdkN` und `main.npdm` aus Ihrem Build-Ordner in den Mod-Ordner von Ryujinx und startet das Spiel. Zu den Optionen gehören zuerst kompilieren, andere Mods deaktivieren und Vollbild.

## Wichtig

Der Editor selbst baut nie für die Switch: Das erledigt die Toolchain Ihres Projekts. Schlägt ein Build fehl, kopieren Sie das Protokoll (es nennt genau Datei und Zeile).
