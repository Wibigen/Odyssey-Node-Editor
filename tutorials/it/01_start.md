# Inizia da qui

**Odyssey Node Editor** ti permette di creare una mod per **Super Mario Odyssey 1.0.0** senza scrivere C++ a mano. Colleghi dei **nodi** su una tela e l'editor scrive per te il codice [exlaunch](https://github.com/shadowninja108/exlaunch). Lo compili comunque con il tuo progetto exlaunch.

## L'idea in un minuto

1. Un nodo **hook** dice *«quando il gioco esegue questa funzione, esegui il mio grafo»*.
2. Poi colleghi altri nodi: chiamare funzioni del gioco, modificare variabili, verificare condizioni, fare cicli.
3. La scheda **Codice C++** mostra il risultato in tempo reale.
4. **Scrivi nel progetto** mette il codice nel tuo progetto exlaunch, **Compila** lo costruisce, la scheda **Ryujinx** avvia il gioco con la tua mod.

## Cosa ti serve

* Una cartella con **OdysseyDecomp** (l'editor legge la sua lista di simboli per conoscere ogni funzione del gioco).
* Un **progetto exlaunch** (per esempio una copia di SMO-Exlaunch-Base) che tu possa compilare.
* *(facoltativo)* Ryujinx, per provare.

## La finestra

| Parte | Cos'è |
|---|---|
| Menu + barra degli strumenti | File, Modifica, Libreria, Visualizza, Strumenti, Plugin, Aiuto; le icone più usate |
| **Blocchi** (sinistra) | Tutti i blocchi che puoi aggiungere, con ricerca |
| **Tela** (centro) | Il tuo grafo |
| **Ispettore** (destra) | Impostazioni del nodo selezionato |
| **Output** (in basso) | Codice C++, Includes, Problemi, Build, Ryujinx |

Usa **Aiuto > Tour dell'interfaccia** per una presentazione guidata, poi segui i tutorial in ordine:

1. *Configura il tuo progetto*
2. *La tua prima mod*
3. *La tela*, poi gli argomenti che ti servono.

**Da sapere:** l'editor non compila mai da solo per la Switch e non tocca mai i file del tuo gioco: scrive C++ nel progetto che gli indichi.
