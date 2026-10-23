# La tela: nodi, pin e collegamenti

## Nodi e pin

Un nodo ha **pin di ingresso** a sinistra e **pin di uscita** a destra.

* I **pin con freccia bianca** sono l'**ordine di esecuzione**: il nodo viene eseguito dopo quello collegato al suo pin *in*, poi prosegue attraverso *next*.
* I **cerchi colorati** sono **valori**. Il colore dipende dal tipo (numero, puntatore, bool, testo…). Un cerchio pieno è collegato; uno vuoto è libero.
* Un ingresso non collegato mostra un **valore fisso** che digiti nell'ispettore (`= 60`).

## Collegare

* **Trascina da un pin a un altro** (un'uscita verso un ingresso).
* Un'uscita di valore può alimentare **più** ingressi; un'uscita di esecuzione porta a **un solo** nodo successivo.
* **Rilascia nel vuoto**: un menu propone *Funzione del gioco…*, *Funzione di plugin…* (quando un plugin ha un catalogo) e tutti i blocchi adatti; il nuovo nodo viene creato e collegato per te. (Si disattiva nelle Preferenze.)
* Seleziona un nodo e premi **Canc** per rimuoverlo; *Ispettore > Scollega* rimuove solo i suoi collegamenti.

## Spostarsi

| Azione | Come |
|---|---|
| Zoom | Rotellina del mouse (Ctrl +/-) |
| Spostare la vista | Tieni premuto il **tasto centrale** e trascina |
| Inquadrare tutto | **F** |
| Selezionarne vari | Trascina un rettangolo su uno spazio vuoto; Ctrl+A per tutti |
| Duplicare / eliminare | Ctrl+D / Canc |
| Annulla / ripeti | Ctrl+Z / Ctrl+Y |
| Trovare un nodo | Ctrl+F nel grafo (l'icona di ricerca) |
| Mettere in ordine | Ctrl+L dispone i nodi automaticamente |

## Aggiungere blocchi

* **Fai doppio clic** o **trascina** un blocco dall'elenco **Blocchi**.
* **Clic destro** sulla tela vuota per le stesse scelte, più *Commenta qui*.
* La casella del filtro sopra l'elenco cerca nei nomi e nelle descrizioni.

## Colori

Ogni tipo di nodo ha il proprio colore di intestazione. I nodi che provengono da un **plugin** hanno anche un morbido alone del colore del plugin, per riconoscerli a colpo d'occhio.
