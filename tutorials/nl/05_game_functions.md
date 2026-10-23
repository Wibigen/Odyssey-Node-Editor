# Spelfuncties aanroepen en hooken

Klik op **Spelfunctie…** (Ctrl+Shift+F) om de catalogus van Super Mario Odyssey-functies te doorzoeken.

## De browser

* Typ een deel van een naam, klasse of beschrijving. Categorieën links beperken de lijst.
* Selecteer een functie om haar **signatuur, retourtype, offset en symbool** te zien.
* De ster ☆ markeert **favorieten**; **Openen op GitHub** opent een zoekopdracht in OdysseyDecomp (handig om te lezen wat ze echt doet).

## Aanroepen of hooken?

| | **Deze functie vanuit mijn mod aanroepen** | **Deze functie hooken** |
|---|---|---|
| Betekenis | *Mijn graaf roept deze spelfunctie aan* | *Wanneer het spel haar aanroept, draait mijn graaf* |
| Node | Een node in je stroom | Een rode ingangsnode (zonder ingang) |
| Typisch gebruik | `al::setPos(actor, …)`, `kill`, een waarde lezen | Je code elk frame uitvoeren, bij een treffer, bij het oppakken van iets |

### Argumenten van een aanroep

Elk argument is ofwel **Een node verbinden** (een waarde aansluiten) of een **Vaste waarde**: een getal, tekst, bool, een `Vector3` (velden X/Y/Z) of een willekeurige C++-expressie.

### Resultaat

Een aanroep die een waarde teruggeeft kan **die in een variabele opslaan** (geef haar een naam in de inspecteur) of **direct als waarde** in een andere node worden gebruikt (*Als waarde gebruiken* in de inspecteur of het rechtsklikmenu).

## Hookmodi

| Modus | Wat er draait |
|---|---|
| **Eerst het origineel, dan mijn graaf** | De spelfunctie, daarna jouw logica (standaard). |
| **Eerst mijn graaf, dan het origineel** | Jouw logica, daarna die van het spel. |
| **Het origineel vervangen** | Alleen jouw graaf. |
| **Handmatig** | Jij plaatst **Call original (Orig)**-nodes waar je wilt in je graaf. |

In de modus *ervoor* met een retourwaarde geeft een uitgang **original result** wat het spel teruggaf. Wijzig zo nodig het retourtype of de argumentnamen in de inspecteur.

## Verkeerd retourtype?

De catalogus raadt retourtypes uit de headers. Zegt een functie `void` maar geeft ze iets terug, gebruik dan **Wijzigen…** naast het retourtype (een waarschuwing vraagt om bevestiging). De keuze wordt onthouden.

## Aanroep op naam

Voor wat niet in de catalogus staat gebruik je **Call by name** (Functies): elke C++-functie op naam, bijv. `sead::Mathf::sqrt(x)`. **Get scene object** dekt `al::getSceneObj<T>(…)`.

## Aanroepstijl

*Voorkeuren > Geavanceerd*: aanroepen zijn standaard gewone C++ (`rs::getPlayerActor(scene)`), of op adres. Eén node kan dit overschrijven (*Aanroepstijl* in de inspecteur). Hooks worden standaard **op symbool** geïnstalleerd; de offsetvorm is de terugvaloptie.
