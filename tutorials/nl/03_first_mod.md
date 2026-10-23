# Je eerste mod

Doel: **één keer per seconde** iets uitvoeren tijdens het spelen. De voorbeeldgraaf doet dit; hier bouw je hem zelf zodat je elk onderdeel kent.

## 1. Een spelfunctie hooken

1. Klik op **Spelfunctie…** (rode knop, of Ctrl+Shift+F).
2. Zoek `exePlay` en selecteer **StageScene::exePlay** (die draait elk frame terwijl je speelt).
3. Kies **Deze functie hooken**, laat de modus *Eerst het origineel, dan mijn graaf* staan en klik op **Aan graaf toevoegen**.

Er verschijnt een rode node **Hook StageScene::exePlay**. De witte pin **next** is waar je logica begint.

## 2. Frames tellen

1. Voeg een **Globale variabele** (Variabelen) toe: type `int`, naam `frames`, beginwaarde `0`. Een globale variabele behoudt haar waarde van het ene frame naar het volgende.
2. Voeg **Set variable** toe, kies `frames` en verbind **hook next → in**.
3. Voeg **Get variable** `frames` en **Math (A + B)** van het type `int`, B = `1`, toe; verbind *Get → A*, *Math out → Set v*.

## 3. Elke 60 frames iets doen

1. Voeg **Branch (if / else)** toe na de Set variable.
2. Voorwaarde: **Compare** `(frames % 60) == 0` (een *Math*-node met `%` en 60 die een *Compare* met `== 0` voedt). Verbind het resultaat met de pin **c** van de Branch.
3. Zet wat je wilt op het pad **then**, bijvoorbeeld een **Custom statement** `/* mijn code hier */`, of een spelfunctie-aanroep.

## 4. De code bekijken

Open het tabblad **C++-code**: de hook, de variabele en de `if` staan erin. Selecteer een node: zijn regels worden gemarkeerd.

## 5. Bouwen en proberen

1. Is het tabblad **Problemen** leeg? Mooi.
2. **Naar project schrijven** (Ctrl+E), daarna **Compileren** (F5).
3. Tabblad **Ryujinx** > *Mod installeren en starten*.

> Sneller starten: **Bestand > Nieuw van sjabloon** (of de voorbeeldgraaf bij Voorkeuren > Openen met) geeft een kant-en-klare graaf.
