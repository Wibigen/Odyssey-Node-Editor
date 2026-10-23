# Spielfunktionen aufrufen und hooken

Klicken Sie auf **Spielfunktion…** (Strg+Umschalt+F), um den Katalog der Super-Mario-Odyssey-Funktionen zu durchsuchen.

## Der Browser

* Tippen Sie einen Teil eines Namens, einer Klasse oder einer Beschreibung. Kategorien links grenzen die Liste ein.
* Wählen Sie eine Funktion, um ihre **Signatur, den Rückgabetyp, den Offset und das Symbol** zu sehen.
* Der Stern ☆ markiert **Favoriten**; **Auf GitHub öffnen** startet eine Suche in OdysseyDecomp (nützlich, um zu lesen, was sie wirklich tut).

## Aufrufen oder hooken?

| | **Diese Funktion aus meinem Mod aufrufen** | **Diese Funktion hooken** |
|---|---|---|
| Bedeutung | *Mein Graph ruft diese Spielfunktion auf* | *Wenn das Spiel sie aufruft, läuft mein Graph* |
| Knoten | Ein Knoten in Ihrem Ablauf | Ein roter Einstiegsknoten (ohne Eingang) |
| Typische Nutzung | `al::setPos(actor, …)`, `kill`, einen Wert lesen | Ihren Code in jedem Frame, bei einem Treffer, beim Einsammeln ausführen |

### Argumente eines Aufrufs

Jedes Argument ist entweder **Knoten verbinden** (einen Wert anschließen) oder ein **Fester Wert**: eine Zahl, Text, ein bool, ein `Vector3` (Felder X/Y/Z) oder ein beliebiger C++-Ausdruck.

### Ergebnis

Ein Aufruf, der einen Wert zurückgibt, kann ihn **in einer Variablen speichern** (im Inspektor benennen) oder **direkt als Wert** in einem anderen Knoten verwendet werden (*Als Wert verwenden* im Inspektor oder im Rechtsklickmenü).

## Hook-Modi

| Modus | Was läuft |
|---|---|
| **Zuerst das Original, dann mein Graph** | Die Spielfunktion, dann Ihre Logik (Standard). |
| **Zuerst mein Graph, dann das Original** | Ihre Logik, dann die des Spiels. |
| **Das Original ersetzen** | Nur Ihr Graph. |
| **Manuell** | Sie setzen **Call original (Orig)**-Knoten dorthin, wo Sie sie in Ihrem Graphen wollen. |

Im Modus *davor* mit Rückgabewert liefert ein Ausgang **original result**, was das Spiel zurückgegeben hat. Ändern Sie bei Bedarf den Rückgabetyp oder die Argumentnamen im Inspektor.

## Falscher Rückgabetyp?

Der Katalog rät Rückgabetypen aus den Headern. Sagt eine Funktion `void`, gibt aber etwas zurück, nutzen Sie **Ändern…** neben dem Rückgabetyp (eine Warnung bittet um Bestätigung). Die Wahl wird gemerkt.

## Aufruf per Name

Für alles, was nicht im Katalog steht, nutzen Sie **Call by name** (Funktionen): jede C++-Funktion per Namen, z. B. `sead::Mathf::sqrt(x)`. **Get scene object** deckt `al::getSceneObj<T>(…)` ab.

## Aufrufstil

*Einstellungen > Erweitert*: Aufrufe sind standardmäßig normales C++ (`rs::getPlayerActor(scene)`) oder per Adresse. Ein einzelner Knoten kann das überschreiben (*Aufrufstil* im Inspektor). Hooks werden standardmäßig **per Symbol** installiert; die Offset-Form ist der Ersatz.
