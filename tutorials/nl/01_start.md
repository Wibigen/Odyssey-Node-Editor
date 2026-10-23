# Begin hier

Met de **Odyssey Node Editor** maak je een mod voor **Super Mario Odyssey 1.0.0** zonder C++ met de hand te schrijven. Je verbindt **nodes** op een canvas en de editor schrijft de [exlaunch](https://github.com/shadowninja108/exlaunch)-code voor je. Je compileert nog steeds met je eigen exlaunch-project.

## Het idee in één minuut

1. Een **hook**-node zegt *„wanneer het spel deze functie uitvoert, voer dan mijn graaf uit”*.
2. Daarna verbind je nodes: spelfuncties aanroepen, variabelen wijzigen, voorwaarden testen, lussen maken.
3. Het tabblad **C++-code** toont het resultaat live.
4. **Naar project schrijven** zet de code in je exlaunch-project, **Compileren** bouwt het, het tabblad **Ryujinx** start het spel met je mod.

## Wat je nodig hebt

* Een map met **OdysseyDecomp** (de editor leest de symbolenlijst om elke spelfunctie te kennen).
* Een **exlaunch-project** (bijvoorbeeld een kopie van SMO-Exlaunch-Base) dat je kunt bouwen.
* *(optioneel)* Ryujinx, om te testen.

## Het venster

| Onderdeel | Wat het is |
|---|---|
| Menu's + werkbalk | Bestand, Bewerken, Bibliotheek, Beeld, Extra, Plugins, Help; de meest gebruikte pictogrammen |
| **Blokken** (links) | Alle blokken die je kunt toevoegen, doorzoekbaar |
| **Canvas** (midden) | Je graaf |
| **Inspecteur** (rechts) | Instellingen van de geselecteerde node |
| **Uitvoer** (onder) | C++-code, Includes, Problemen, Build, Ryujinx |

Kies **Help > Rondleiding door de interface** voor een rondleiding en volg daarna de tutorials in volgorde:

1. *Je project instellen*
2. *Je eerste mod*
3. *Het canvas*, daarna de onderwerpen die je nodig hebt.

**Goed om te weten:** de editor compileert nooit zelf voor de Switch en raakt je spelbestanden nooit aan: hij schrijft C++ in het project waar je hem naartoe wijst.
