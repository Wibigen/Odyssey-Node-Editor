# Variabili, valori e matematica

## Variabili (categoria *Variabili*)

| Blocco | Uso |
|---|---|
| **Declare variable** | Una variabile locale (tipo, nome, valore iniziale facoltativo). Vive nel flusso in cui la dichiari. |
| **Set variable** | Assegnare un nuovo valore. |
| **Get variable** | Leggere il valore attuale (un'uscita di valore, senza pin di esecuzione). |
| **Global variable** | Mantiene il valore tra fotogrammi e chiamate. Un *Declare variable* fuori da una funzione diventa anch'esso globale. |
| **Constant (value)** | Un numero, testo, bool o qualsiasi valore C++ che digiti. |

Usa **Avanzate** nell'ispettore per i qualificatori (`static`, `const`…) e gli array (dimensione e contenuto).

> Una variabile locale dichiarata dentro un ramo esiste solo in quel ramo (come in C++).

## Matematica e logica

Disegnati come piccoli quadrati:

* **Math (A + B)**: `+ - * / %` su due valori (scegli il tipo).
* **Compare**: `== != < > <= >=`, dà un bool.
* **Logic**: AND / OR; **NOT** inverte un bool.

Collega il risultato alla condizione di un **Branch**, a una variabile o a un argomento di una chiamata.

## Valore fisso o collegamento?

Qualsiasi pin di ingresso può essere **collegato** a un nodo oppure ricevere un **valore fisso** (digitalo nell'ispettore). Un ingresso collegato nasconde il proprio valore fisso.

## Tipi

I colori dei pin indicano i tipi; l'editor non verifica i tipi dei puntatori tra i collegamenti (per esempio `StageScene*` verso `al::LiveActor*` è un errore C++ che vedrai in fase di build). Usa **Cast** (Puntatori e memoria) quando devi convertire.
