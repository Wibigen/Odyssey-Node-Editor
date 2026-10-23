# Ablaufsteuerung

Die **Flow**-Blöcke entscheiden, *welche* Knoten laufen und *wie oft*.

| Block | Was er tut |
|---|---|
| **Branch (if / else)** | Bedingung **c**: führt den Pfad **then** oder den Pfad **else** aus und geht dann weiter. |
| **Switch** | Wählt einen Pfad anhand eines Ganzzahlwerts; die Fälle bearbeiten Sie als kleine Felder mit der Schaltfläche **+**. |
| **For loop** | Wiederholt einen Pfad N-mal; der Index ist ein Ausgang. |
| **While loop** | Wiederholt, solange eine Bedingung wahr ist. |
| **Return** | Verlässt die aktuelle Funktion oder den Hook, optional mit einem Wert. |

## Den Ablauf lesen

Folgen Sie den weißen Pfeilen. Ein Knoten mit zwei Pfeilausgängen (Branch) hat zwei mögliche Fortsetzungen; beide können danach in einem gemeinsamen Knoten münden.

## Tipps

* Halten Sie Schleifen kurz: Hooks laufen im Hauptthread des Spiels, in jedem Frame.
* Um etwas **einmal** pro Bedingungswechsel zu tun, speichern Sie den vorherigen Zustand in einer **Globalen Variablen**.
* Fassen Sie eine wiederkehrende Idee in einer eigenen Funktion zusammen (nächstes Tutorial).
