# Code, problemen en bouwen

Het paneel **Uitvoer** onderaan heeft vijf tabbladen. Klap het in met de pijl, **Ctrl+J** of een dubbelklik op een tabblad.

## C++-code

Live voorbeeld van het gegenereerde bestand. De regels van de **geselecteerde node** zijn gemarkeerd. **Kopiëren** en **Opslaan als…** exporteren het.

## Includes

De headers bovenaan het bestand (zie *Eigen code*).

## Problemen

Wat er ontbreekt of fout is **voordat** je compileert: niet-verbonden ingangen, onbekende variabelen, lege hooks. Dubbelklik op een regel om naar de node te springen.

## Build

* **Naar project schrijven** (Ctrl+E) slaat de code op in je exlaunch-project.
* **Compileren** (F5) voert het buildcommando uit en toont de uitvoer. **Fouten kopiëren** kopieert alleen de foutregels; **Buildlogboek opslaan** bewaart de hele console.
* **Basis herstellen** (menu Extra) verwijdert `build/` en voert CMake opnieuw uit.

## Ryujinx

Stel de emulator, het spelbestand en een modnaam één keer in. **Mod installeren en starten** kopieert `subsdkN` en `main.npdm` uit je buildmap naar de modmap van Ryujinx en start het spel. Opties zijn onder meer eerst compileren, andere mods uitschakelen en volledig scherm.

## Belangrijk

De editor zelf bouwt nooit voor de Switch: dat doet de toolchain van je project. Als een build mislukt, kopieer dan het logboek (daar staat precies welk bestand en welke regel).
