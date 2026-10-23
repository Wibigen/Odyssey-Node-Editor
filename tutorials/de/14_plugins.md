# Plugins

Plugins fügen **Knoten**, **Funktionskataloge**, **Designs**, **Vorlagen** und **Tutorials** hinzu.

## Plugin-Explorer

**Plugins > Plugin-Explorer** (Strg+Umschalt+P): jedes Plugin mit Bild, Autor, Version und Inhalt. **Aktivieren / Deaktivieren**, **Installieren…** (eine `.zip` / `.odnp` oder ein Ordner), **Entfernen**, **Neues Plugin…** (ein Grundgerüst zum Bearbeiten), **Ordner anzeigen**.

Mitgeliefert: *Standard-Ein-/Ausgabe*, *Zeichenketten*, *Zusätzliche Designs* und **Dear ImGui** (standardmäßig aus).

## Nutzen, was ein Plugin hinzufügt

* Knoten erscheinen in der Liste **Blöcke** unter den Kategorien des Plugins, mit einem sanften farbigen Schimmer auf der Zeichenfläche.
* Ein Katalog öffnet sich mit **Plugin-Funktion…** (Strg+Umschalt+K, dem Knopf über der Blockliste oder dem Menü bei einer losgelassenen Verbindung).
* Vorlagen: **Datei > Neu aus Vorlage**.
* Tutorials: Fenster **Tutorials**, Abschnitt *Plugin-Tutorials*.

## Plugins, die Ihr Projekt ändern

Manche Plugins (Dear ImGui) brauchen Dateien und CMake-Zeilen in Ihrem exlaunch-Projekt. Der Editor **bietet** das beim Aktivieren **an**: Nichts wird überschrieben, eine Sicherung von `CMakeLists.txt` bleibt erhalten, und *Plugin-Explorer > exlaunch-Basis…* entfernt genau das Hinzugefügte.

## Sicherheit

Ein Plugin mit einer Datei `plugin.py` führt Python mit denselben Rechten wie der Editor aus. Installieren Sie nur Plugins von vertrauenswürdigen Personen.

## Selbst eines schreiben

Siehe `PLUGINS.md` (Format, Knotenvorlagen, Designs, Hilfeseiten, Einstellungen).
