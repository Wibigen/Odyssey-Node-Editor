# Plugins

Plugins voegen **nodes**, **functiecatalogi**, **thema's**, **sjablonen** en **tutorials** toe.

## Pluginverkenner

**Plugins > Pluginverkenner** (Ctrl+Shift+P): elke plugin met afbeelding, auteur, versie en inhoud. **Inschakelen / Uitschakelen**, **Installeren…** (een `.zip` / `.odnp` of een map), **Verwijderen**, **Nieuwe plugin…** (een skelet om te bewerken), **Map tonen**.

Meegeleverd: *Standaard in-/uitvoer*, *Strings*, *Extra thema's* en **Dear ImGui** (standaard uit).

## Gebruiken wat een plugin toevoegt

* Nodes verschijnen in de lijst **Blokken** onder de categorieën van de plugin, met een zachte gekleurde gloed op het canvas.
* Een catalogus opent met **Pluginfunctie…** (Ctrl+Shift+K, de knop boven de blokkenlijst of het menu bij een losgelaten koppeling).
* Sjablonen: **Bestand > Nieuw van sjabloon**.
* Tutorials: venster **Tutorials**, sectie *Plugin-tutorials*.

## Plugins die je project wijzigen

Sommige plugins (Dear ImGui) hebben bestanden en CMake-regels in je exlaunch-project nodig. De editor **biedt** dit bij het inschakelen **aan**: er wordt niets overschreven, een back-up van `CMakeLists.txt` blijft bewaard en *Pluginverkenner > exlaunch-basis…* verwijdert precies wat is toegevoegd.

## Veiligheid

Een plugin met een bestand `plugin.py` voert Python uit met dezelfde rechten als de editor. Installeer alleen plugins van mensen die je vertrouwt.

## Er zelf een schrijven

Zie `PLUGINS.md` (formaat, nodesjablonen, thema's, helppagina's, instellingen).
