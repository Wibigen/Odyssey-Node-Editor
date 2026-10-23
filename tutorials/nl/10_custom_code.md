# Eigen code en C++ importeren

Nodes dekken veel, maar niet alles. Twee nooduitgangen houden je op gang.

## Eigen blokken

* **Custom expression**: een willekeurige C++-expressie die als waarde wordt gebruikt.
* **Custom statement**: een willekeurige C++-instructie in de stroom.

Verbind tot acht ingangen en verwijs ernaar als `$a` … `$h` in je tekst:

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## Include-bestanden

Het tabblad **Includes** (onderaan) toont de `#include`-regels van het gegenereerde bestand. Voeg de headers toe die je eigen code nodig heeft.

## C++ importeren

**Bestand > C++-bestand importeren…** (Ctrl+I) zet een `.cpp` om in een graaf voor zover hij het begrijpt. Hij leest de code die dit hulpmiddel schrijft en gangbare met de hand geschreven patronen; templates, klassen en ongebruikelijke macro's blijven eigen code. Controleer daarna het tabblad *Problemen*.
