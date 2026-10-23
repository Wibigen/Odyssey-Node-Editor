# Fehlerbehebung

| Problem | Was Sie versuchen können |
|---|---|
| *Der Funktionskatalog ist leer* | Werkzeuge > Einstellungen: Wählen Sie Ihren OdysseyDecomp-Ordner (mit `data/file_list.yml`) und extrahieren Sie den Katalog. |
| Eine Funktion gibt `void` zurück, sollte aber nicht | Ändern Sie den Rückgabetyp (siehe *Spielfunktionen aufrufen und hooken*). |
| Der Reiter *Probleme* listet etwas auf | Doppelklicken Sie auf eine Zeile: Der Knoten wird ausgewählt. Meist ein nicht verbundener Eingang oder eine fehlende Variable. |
| Der Compiler findet einen Header nicht | Fügen Sie ihn im Reiter **Includes** hinzu oder korrigieren Sie die Include-Ordner Ihres Projekts. |
| Der Build-Ordner ist defekt | Werkzeuge > **exlaunch-Basis reparieren**. |
| Im Spiel passiert nichts | Ist der Hook installiert (richtiges Symbol)? Ist der Mod-Ordner der, den Ryujinx lädt (Reiter Ryujinx)? Ist ein anderer Mod deaktiviert? |
| Das Spiel stürzt ab | Ein Zeiger ist null oder ein Offset ist falsch. Fügen Sie **Is null?**-Prüfungen hinzu; bestätigen Sie die Offsets für Version 1.0.0. |
| Ein Kürzel funktioniert nicht | Werkzeuge > Tastenkürzel: Es wurde eventuell geändert. |
| Das Fensterlayout ist seltsam | Ansicht: Zeigen Sie den Ausgabebereich (Strg+J); ziehen Sie die Bereiche dorthin zurück, wo Sie sie haben möchten. |

Wenn Sie ein Problem melden, fügen Sie das **Build**-Protokoll bei (Build-Protokoll speichern).
