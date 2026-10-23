# Hier beginnen

Mit dem **Odyssey Node Editor** erstellen Sie einen Mod für **Super Mario Odyssey 1.0.0**, ohne C++ von Hand zu schreiben. Sie verbinden **Knoten** auf einer Zeichenfläche, und der Editor schreibt den [exlaunch](https://github.com/shadowninja108/exlaunch)-Code für Sie. Kompiliert wird weiterhin mit Ihrem eigenen exlaunch-Projekt.

## Die Idee in einer Minute

1. Ein **Hook**-Knoten sagt *„Wenn das Spiel diese Funktion ausführt, führe meinen Graphen aus“*.
2. Danach verbinden Sie Knoten: Spielfunktionen aufrufen, Variablen ändern, Bedingungen prüfen, Schleifen bilden.
3. Der Reiter **C++-Code** zeigt das Ergebnis live.
4. **Ins Projekt schreiben** legt den Code in Ihrem exlaunch-Projekt ab, **Kompilieren** baut ihn, der Reiter **Ryujinx** startet das Spiel mit Ihrem Mod.

## Was Sie brauchen

* Einen Ordner mit **OdysseyDecomp** (der Editor liest dessen Symbolliste, um jede Spielfunktion zu kennen).
* Ein **exlaunch-Projekt** (zum Beispiel eine Kopie von SMO-Exlaunch-Base), das Sie bauen können.
* *(optional)* Ryujinx zum Testen.

## Das Fenster

| Bereich | Was es ist |
|---|---|
| Menüs + Werkzeugleiste | Datei, Bearbeiten, Bibliothek, Ansicht, Werkzeuge, Plugins, Hilfe; die am häufigsten genutzten Symbole |
| **Blöcke** (links) | Alle Blöcke, die Sie hinzufügen können, mit Suche |
| **Zeichenfläche** (Mitte) | Ihr Graph |
| **Inspektor** (rechts) | Einstellungen des ausgewählten Knotens |
| **Ausgabe** (unten) | C++-Code, Includes, Probleme, Build, Ryujinx |

Starten Sie mit **Hilfe > Rundgang durch die Oberfläche** eine geführte Vorstellung und folgen Sie dann den Tutorials der Reihe nach:

1. *Ihr Projekt einrichten*
2. *Ihr erster Mod*
3. *Die Zeichenfläche*, danach die Themen, die Sie brauchen.

**Gut zu wissen:** Der Editor kompiliert nie selbst für die Switch und fasst Ihre Spieldateien nie an: Er schreibt C++ in das Projekt, auf das Sie ihn verweisen.
