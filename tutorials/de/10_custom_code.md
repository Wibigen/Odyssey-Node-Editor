# Eigener Code und C++-Import

Knoten decken viel ab, aber nicht alles. Zwei Notausgänge halten Sie in Bewegung.

## Eigene Blöcke

* **Custom expression**: ein beliebiger C++-Ausdruck, der als Wert verwendet wird.
* **Custom statement**: eine beliebige C++-Anweisung im Ablauf.

Verbinden Sie bis zu acht Eingänge und verweisen Sie in Ihrem Text mit `$a` … `$h` darauf:

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## Include-Dateien

Der Reiter **Includes** (unten) listet die `#include`-Zeilen der erzeugten Datei. Fügen Sie die Header hinzu, die Ihr eigener Code braucht.

## C++ importieren

**Datei > C++-Datei importieren…** (Strg+I) wandelt eine `.cpp` in einen Graphen um, soweit er sie versteht. Er liest den Code, den dieses Werkzeug schreibt, und verbreitete handgeschriebene Muster; Templates, Klassen und ungewöhnliche Makros bleiben als eigener Code erhalten. Prüfen Sie danach den Reiter *Probleme*.
