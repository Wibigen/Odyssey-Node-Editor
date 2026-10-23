# Ihr erster Mod

Ziel: **einmal pro Sekunde** während des Spiels etwas ausführen. Der Beispielgraph macht das; hier bauen Sie ihn selbst, damit Sie jeden Teil kennen.

## 1. Eine Spielfunktion hooken

1. Klicken Sie auf **Spielfunktion…** (roter Knopf, oder Strg+Umschalt+F).
2. Suchen Sie `exePlay` und wählen Sie **StageScene::exePlay** (sie läuft in jedem Frame, während Sie spielen).
3. Wählen Sie **Diese Funktion hooken**, behalten Sie den Modus *Zuerst das Original, dann mein Graph* und klicken Sie auf **Zum Graphen hinzufügen**.

Ein roter Knoten **Hook StageScene::exePlay** erscheint. Sein weißer Pin **next** ist der Startpunkt Ihrer Logik.

## 2. Frames zählen

1. Fügen Sie eine **Globale Variable** (Variablen) hinzu: Typ `int`, Name `frames`, Anfangswert `0`. Eine globale Variable behält ihren Wert von einem Frame zum nächsten.
2. Fügen Sie **Set variable** hinzu, wählen Sie `frames` und verbinden Sie **hook next → in**.
3. Fügen Sie **Get variable** `frames` und **Math (A + B)** vom Typ `int`, B = `1`, hinzu; verbinden Sie *Get → A*, *Math out → Set v*.

## 3. Alle 60 Frames etwas tun

1. Fügen Sie nach dem Set variable ein **Branch (if / else)** hinzu.
2. Bedingung: **Compare** `(frames % 60) == 0` (ein *Math*-Knoten mit `%` und 60, der in einen *Compare* mit `== 0` führt). Verbinden Sie das Ergebnis mit dem Pin **c** des Branch.
3. Legen Sie auf den Pfad **then**, was Sie möchten, zum Beispiel ein **Custom statement** `/* mein Code hier */` oder einen Spielfunktionsaufruf.

## 4. Den Code ansehen

Öffnen Sie den Reiter **C++-Code**: Hook, Variable und das `if` sind dort. Wählen Sie einen Knoten: Seine Zeilen werden hervorgehoben.

## 5. Bauen und ausprobieren

1. Der Reiter **Probleme** ist leer? Gut.
2. **Ins Projekt schreiben** (Strg+E), dann **Kompilieren** (F5).
3. Reiter **Ryujinx** > *Mod installieren und starten*.

> Schneller Start: **Datei > Neu aus Vorlage** (oder der Beispielgraph unter Einstellungen > Öffnen mit) liefert einen fertigen Graphen.
