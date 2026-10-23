# Variablen, Werte und Mathematik

## Variablen (Kategorie *Variablen*)

| Block | Verwendung |
|---|---|
| **Declare variable** | Eine lokale Variable (Typ, Name, optionaler Anfangswert). Lebt in dem Ablauf, in dem Sie sie deklarieren. |
| **Set variable** | Einen neuen Wert zuweisen. |
| **Get variable** | Den aktuellen Wert lesen (ein Werteausgang, ohne Ausführungspin). |
| **Global variable** | Behält ihren Wert zwischen Frames und Aufrufen. Ein *Declare variable* außerhalb einer Funktion wird ebenfalls global. |
| **Constant (value)** | Eine feste Zahl, Text, bool oder ein beliebiger C++-Wert, den Sie eintippen. |

Nutzen Sie **Erweitert** im Inspektor für Qualifizierer (`static`, `const` …) und Arrays (Größe und Inhalt).

> Eine in einem Zweig deklarierte lokale Variable existiert nur in diesem Zweig (wie in C++).

## Mathe und Logik

Als kleine Quadrate dargestellt:

* **Math (A + B)**: `+ - * / %` auf zwei Werten (Typ wählen).
* **Compare**: `== != < > <= >=`, liefert ein bool.
* **Logic**: AND / OR; **NOT** invertiert ein bool.

Verbinden Sie das Ergebnis mit der Bedingung eines **Branch**, einer Variablen oder einem Argument eines Aufrufs.

## Fester Wert oder Verbindung?

Jeder Eingangspin kann mit einem Knoten **verbunden** oder mit einem **festen Wert** versehen werden (im Inspektor eintippen). Ein verbundener Eingang verbirgt seinen festen Wert.

## Typen

Pinfarben zeigen Typen; der Editor prüft Zeigertypen zwischen Verbindungen nicht (zum Beispiel ist `StageScene*` in `al::LiveActor*` ein C++-Fehler, den Sie beim Build sehen). Nutzen Sie **Cast** (Zeiger und Speicher), wenn Sie umwandeln müssen.
