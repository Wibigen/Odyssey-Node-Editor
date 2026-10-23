# Je project instellen

Open **Extra > Instellingen** (Ctrl+Shift+,). Het venster opent de eerste keer vanzelf.

## 1. De OdysseyDecomp-map

Kies de map van je kopie van [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) (die met `data/file_list.yml`). De editor bouwt dan de **functiecatalogus** (ongeveer 17.700 functies): namen, argumenten, retourtypes, offsets en symbolen. Dit gebeurt één keer en wordt opgeslagen. Voor het lezen van gemangelde namen is het hulpprogramma `c++filt` nodig; het wordt automatisch gevonden, of je geeft het op in hetzelfde venster.

Als de catalogus `void` aangeeft voor een functie die in werkelijkheid iets teruggeeft, kun je dat later corrigeren (zie *Spelfuncties aanroepen en hooken*).

## 2. Je exlaunch-project

* **Projectmap**: de hoofdmap van je exlaunch-project (die met `CMakeLists.txt`). Windows-paden, `\\wsl$\Ubuntu\home\me\proj` en WSL-paden worden begrepen.
* **Gegenereerd bestand**: waar de code naartoe wordt geschreven. Leeg = `src/program/main.cpp` of `src/main.cpp`, wat er bestaat.

## 3. Het buildcommando

Standaard: `cmake --build build`. Kies waar het draait: **Windows (cmd)**, **WSL** (kies de distributie, bijvoorbeeld Ubuntu) of de eigen shell. De eerste keer *Compileren* wordt erom gevraagd als het niet is ingesteld.

## 4. Testen

Open het tabblad **Ryujinx** (onderaan) en stel één keer het Ryujinx-programma, het spelbestand en een modnaam in. *Mod installeren en starten* kopieert je build naar de modmap van Ryujinx en start het spel.

## Als iets niet wordt gevonden

* Tabblad **Problemen**: wat de graaf nog nodig heeft.
* **Extra > exlaunch-basis herstellen**: verwijdert de map `build` en voert CMake opnieuw uit (herstelt een kapotte opzet).
* De Instellingen kunnen op elk moment opnieuw worden geopend; er gaat niets verloren.
