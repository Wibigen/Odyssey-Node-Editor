# Die Zeichenfläche: Knoten, Pins und Verbindungen

## Knoten und Pins

Ein Knoten hat **Eingangspins** links und **Ausgangspins** rechts.

* **Pins mit weißem Pfeil** sind die **Ausführungsreihenfolge**: Der Knoten läuft nach dem Knoten, der mit seinem Pin *in* verbunden ist, und geht dann über *next* weiter.
* **Farbige Kreise** sind **Werte**. Die Farbe hängt vom Typ ab (Zahl, Zeiger, bool, Text …). Ein gefüllter Kreis ist verbunden; ein leerer ist frei.
* Ein nicht verbundener Eingang zeigt einen **festen Wert**, den Sie im Inspektor eingeben (`= 60`).

## Verbinden

* **Ziehen Sie von einem Pin zu einem anderen** (ein Ausgang zu einem Eingang).
* Ein Werteausgang kann **mehrere** Eingänge speisen; ein Ausführungsausgang führt zu **einem** nächsten Knoten.
* **Auf leerer Fläche loslassen**: Ein Menü bietet *Spielfunktion…*, *Plugin-Funktion…* (wenn ein Plugin einen Katalog hat) und alle passenden Blöcke; der neue Knoten wird für Sie erstellt und verbunden. (In den Einstellungen abschaltbar.)
* Wählen Sie einen Knoten und drücken Sie **Entf**, um ihn zu entfernen; *Inspektor > Trennen* entfernt nur seine Verbindungen.

## Navigieren

| Aktion | So geht's |
|---|---|
| Zoomen | Mausrad (Strg +/-) |
| Verschieben | **Mittlere Taste** halten und ziehen |
| Alles einpassen | **F** |
| Mehrere auswählen | Rechteck auf leerer Fläche aufziehen; Strg+A für alle |
| Duplizieren / Löschen | Strg+D / Entf |
| Rückgängig / Wiederholen | Strg+Z / Strg+Y |
| Knoten finden | Strg+F im Graphen (das Suchsymbol) |
| Aufräumen | Strg+L ordnet die Knoten automatisch an |

## Blöcke hinzufügen

* **Doppelklicken** oder **ziehen** Sie einen Block aus der Liste **Blöcke**.
* **Rechtsklick** auf die leere Fläche bietet dieselben Möglichkeiten, dazu *Hier kommentieren*.
* Das Filterfeld über der Liste durchsucht Namen und Beschreibungen.

## Farben

Jede Knotenart hat ihre eigene Kopfzeilenfarbe. Knoten, die von einem **Plugin** stammen, haben zusätzlich einen sanften Schimmer in der Farbe des Plugins, damit Sie sie auf einen Blick erkennen.
