# Controllo del flusso

I blocchi **Flow** decidono *quali* nodi vengono eseguiti e *quante volte*.

| Blocco | Cosa fa |
|---|---|
| **Branch (if / else)** | Condizione **c**: esegue il percorso **then** o il percorso **else**, poi prosegue. |
| **Switch** | Sceglie un percorso da un valore intero; modifica i casi come piccole caselle con il pulsante **+**. |
| **For loop** | Ripete un percorso N volte; l'indice è un'uscita. |
| **While loop** | Ripete finché una condizione è vera. |
| **Return** | Esce dalla funzione o dall'hook corrente, facoltativamente con un valore. |

## Leggere il flusso

Segui le frecce bianche. Un nodo con due uscite a freccia (Branch) ha due possibili passi successivi; entrambi possono poi proseguire verso un nodo comune.

## Consigli

* Tieni breve un ciclo: gli hook vengono eseguiti sul thread principale del gioco, a ogni fotogramma.
* Per fare qualcosa **una sola volta** a ogni cambio di condizione, memorizza lo stato precedente in una **Variabile globale**.
* Racchiudi un'idea ripetuta in una funzione tutta tua (prossimo tutorial).
