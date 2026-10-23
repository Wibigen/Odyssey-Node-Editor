# Variabelen, waarden en wiskunde

## Variabelen (categorie *Variabelen*)

| Blok | Gebruik |
|---|---|
| **Declare variable** | Een lokale variabele (type, naam, optionele beginwaarde). Leeft in de stroom waarin je haar declareert. |
| **Set variable** | Een nieuwe waarde toekennen. |
| **Get variable** | De huidige waarde lezen (een waardeuitgang, zonder uitvoeringspin). |
| **Global variable** | Behoudt haar waarde tussen frames en aanroepen. Een *Declare variable* buiten een functie wordt ook globaal. |
| **Constant (value)** | Een vast getal, tekst, bool of een willekeurige C++-waarde die je typt. |

Gebruik **Geavanceerd** in de inspecteur voor kwalificaties (`static`, `const`…) en arrays (grootte en inhoud).

> Een lokale variabele die in een tak is gedeclareerd bestaat alleen in die tak (zoals in C++).

## Wiskunde en logica

Getekend als kleine vierkantjes:

* **Math (A + B)**: `+ - * / %` op twee waarden (kies het type).
* **Compare**: `== != < > <= >=`, geeft een bool.
* **Logic**: AND / OR; **NOT** keert een bool om.

Verbind het resultaat met de voorwaarde van een **Branch**, een variabele of een argument van een aanroep.

## Vaste waarde of koppeling?

Elke ingangspin kan met een node worden **verbonden** of een **vaste waarde** krijgen (typ die in de inspecteur). Een verbonden ingang verbergt zijn vaste waarde.

## Types

Pinkleuren tonen types; de editor controleert pointertypes tussen koppelingen niet (bijvoorbeeld `StageScene*` naar `al::LiveActor*` is een C++-fout die je bij het bouwen ziet). Gebruik **Cast** (Pointers en geheugen) als je moet converteren.
