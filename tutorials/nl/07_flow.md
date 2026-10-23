# Stroomregeling

De **Flow**-blokken bepalen *welke* nodes draaien en *hoe vaak*.

| Blok | Wat het doet |
|---|---|
| **Branch (if / else)** | Voorwaarde **c**: voert het pad **then** of het pad **else** uit en gaat daarna verder. |
| **Switch** | Kiest een pad uit een geheel getal; bewerk de gevallen als kleine vakjes met de knop **+**. |
| **For loop** | Herhaalt een pad N keer; de index is een uitgang. |
| **While loop** | Herhaalt zolang een voorwaarde waar is. |
| **Return** | Verlaat de huidige functie of hook, eventueel met een waarde. |

## De stroom lezen

Volg de witte pijlen. Een node met twee pijluitgangen (Branch) heeft twee mogelijke vervolgstappen; beide kunnen daarna samenkomen in een gemeenschappelijke node.

## Tips

* Houd een lus kort: hooks draaien op de hoofdthread van het spel, elk frame.
* Om iets **één keer** te doen per voorwaardewijziging, bewaar je de vorige toestand in een **Globale variabele**.
* Verpak een terugkerend idee in je eigen functie (volgende tutorial).
