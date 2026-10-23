# Chiamare e agganciare funzioni del gioco

Fai clic su **Funzione del gioco…** (Ctrl+Maiusc+F) per cercare nel catalogo delle funzioni di Super Mario Odyssey.

## Il browser

* Digita parte di un nome, di una classe o di una descrizione. Le categorie a sinistra restringono l'elenco.
* Seleziona una funzione per vederne **firma, tipo di ritorno, offset e simbolo**.
* La stella ☆ indica i **preferiti**; **Apri su GitHub** apre una ricerca in OdysseyDecomp (utile per leggere cosa fa davvero).

## Chiamare o agganciare?

| | **Chiama questa funzione dalla mia mod** | **Aggancia questa funzione** |
|---|---|---|
| Significato | *Il mio grafo chiama questa funzione del gioco* | *Quando il gioco la chiama, il mio grafo viene eseguito* |
| Nodo | Un nodo dentro il tuo flusso | Un nodo d'ingresso rosso (senza ingresso) |
| Uso tipico | `al::setPos(actor, …)`, `kill`, leggere un valore | Eseguire il tuo codice a ogni fotogramma, a un colpo, a una raccolta |

### Argomenti di una chiamata

Ogni argomento è o **Collega un nodo** (collegare un valore) o un **Valore fisso**: un numero, testo, bool, un `Vector3` (campi X/Y/Z) o qualsiasi espressione C++.

### Risultato

Una chiamata che restituisce un valore può **salvarlo in una variabile** (dagli un nome nell'ispettore) oppure essere usata **direttamente come valore** dentro un altro nodo (*Usa come valore* nell'ispettore o nel menu del clic destro).

## Modalità dell'hook

| Modalità | Cosa viene eseguito |
|---|---|
| **Esegui prima l'originale, poi il mio grafo** | La funzione del gioco, poi la tua logica (predefinito). |
| **Esegui prima il mio grafo, poi l'originale** | La tua logica, poi quella del gioco. |
| **Sostituisci l'originale** | Solo il tuo grafo. |
| **Manuale** | Metti tu i nodi **Call original (Orig)** dove vuoi nel tuo grafo. |

In modalità *prima* con un valore di ritorno, un'uscita **original result** ti dà ciò che il gioco ha restituito. Cambia il tipo di ritorno o i nomi degli argomenti nell'ispettore se serve.

## Tipo di ritorno sbagliato?

Il catalogo deduce i tipi di ritorno dagli header. Se una funzione dice `void` ma restituisce qualcosa, usa **Cambia…** accanto al tipo di ritorno (un avviso chiede conferma). La scelta viene ricordata.

## Chiamata per nome

Per ciò che non è nel catalogo usa **Call by name** (Funzioni): qualsiasi funzione C++ scritta per nome, ad es. `sead::Mathf::sqrt(x)`. **Get scene object** copre `al::getSceneObj<T>(…)`.

## Stile di chiamata

*Preferenze > Avanzate*: le chiamate sono C++ normale per impostazione predefinita (`rs::getPlayerActor(scene)`), oppure per indirizzo. Un singolo nodo può sovrascriverlo (*Stile di chiamata* nell'ispettore). Gli hook si installano **per simbolo** in modo predefinito; la forma per offset è l'alternativa.
