# Probleemoplossing

| Probleem | Wat je kunt proberen |
|---|---|
| *De functiecatalogus is leeg* | Extra > Instellingen: kies je OdysseyDecomp-map (met `data/file_list.yml`) en haal de catalogus uit. |
| Een functie geeft `void` terug maar zou dat niet moeten | Wijzig het retourtype (zie *Spelfuncties aanroepen en hooken*). |
| Het tabblad *Problemen* toont iets | Dubbelklik op een regel: de node wordt geselecteerd. Meestal een niet-verbonden ingang of een ontbrekende variabele. |
| Compileren vindt een header niet | Voeg hem toe in het tabblad **Includes**, of corrigeer de include-mappen van je project. |
| De buildmap is kapot | Extra > **exlaunch-basis herstellen**. |
| Er gebeurt niets in het spel | Is de hook geïnstalleerd (juist symbool)? Is de modmap degene die Ryujinx laadt (tabblad Ryujinx)? Is een andere mod uitgeschakeld? |
| Het spel crasht | Een pointer is null of een offset klopt niet. Voeg **Is null?**-controles toe; bevestig de offsets voor versie 1.0.0. |
| Een sneltoets werkt niet | Extra > Sneltoetsen: hij kan gewijzigd zijn. |
| De vensterindeling is vreemd | Beeld: toon het uitvoerpaneel (Ctrl+J); sleep de panelen terug waar je ze wilt. |

Als je een probleem meldt, voeg dan het **Build**-logboek bij (Buildlogboek opslaan).
