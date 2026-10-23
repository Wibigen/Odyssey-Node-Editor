# Het canvas: nodes, pins en koppelingen

## Nodes en pins

Een node heeft **ingangspins** links en **uitgangspins** rechts.

* **Pins met een witte pijl** zijn de **uitvoeringsvolgorde**: de node draait na de node die met zijn pin *in* is verbonden en gaat daarna verder via *next*.
* **Gekleurde cirkels** zijn **waarden**. De kleur hangt af van het type (getal, pointer, bool, tekst…). Een gevulde cirkel is verbonden; een lege is vrij.
* Een niet-verbonden ingang toont een **vaste waarde** die je in de inspecteur typt (`= 60`).

## Verbinden

* **Sleep van een pin naar een andere pin** (een uitgang naar een ingang).
* Een waardeuitgang kan **meerdere** ingangen voeden; een uitvoeringsuitgang gaat naar **één** volgende node.
* **Loslaten op een lege plek**: een menu biedt *Spelfunctie…*, *Pluginfunctie…* (wanneer een plugin een catalogus heeft) en alle blokken die passen; de nieuwe node wordt voor je aangemaakt en verbonden. (Uit te zetten in de Voorkeuren.)
* Selecteer een node en druk op **Delete** om hem te verwijderen; *Inspecteur > Loskoppelen* verwijdert alleen zijn koppelingen.

## Navigeren

| Actie | Hoe |
|---|---|
| Zoomen | Muiswiel (Ctrl +/-) |
| Verschuiven | Houd de **middelste knop** ingedrukt en sleep |
| Alles in beeld | **F** |
| Meerdere selecteren | Sleep een rechthoek op een lege plek; Ctrl+A voor alles |
| Dupliceren / verwijderen | Ctrl+D / Delete |
| Ongedaan maken / opnieuw | Ctrl+Z / Ctrl+Y |
| Een node zoeken | Ctrl+F in de graaf (het zoekpictogram) |
| Opruimen | Ctrl+L rangschikt de nodes automatisch |

## Blokken toevoegen

* **Dubbelklik** op een blok of **sleep** het uit de lijst **Blokken**.
* **Rechtsklik** op het lege canvas voor dezelfde keuzes, plus *Hier commentaar toevoegen*.
* Het filtervak boven de lijst doorzoekt namen en beschrijvingen.

## Kleuren

Elke soort node heeft zijn eigen kopkleur. Nodes die van een **plugin** komen hebben bovendien een zachte gloed in de kleur van de plugin, zodat je ze in één oogopslag herkent.
