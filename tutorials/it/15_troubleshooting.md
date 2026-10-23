# Risoluzione dei problemi

| Problema | Cosa provare |
|---|---|
| *Il catalogo delle funzioni è vuoto* | Strumenti > Impostazioni: scegli la tua cartella OdysseyDecomp (con `data/file_list.yml`) ed estrai il catalogo. |
| Una funzione restituisce `void` ma non dovrebbe | Cambia il tipo di ritorno (vedi *Chiamare e agganciare funzioni del gioco*). |
| La scheda *Problemi* elenca qualcosa | Fai doppio clic su una riga: il nodo viene selezionato. Di solito un ingresso non collegato o una variabile mancante. |
| La compilazione non trova un header | Aggiungilo nella scheda **Includes**, oppure correggi le cartelle di inclusione del tuo progetto. |
| La cartella di build è danneggiata | Strumenti > **Ripara la base exlaunch**. |
| Nel gioco non succede nulla | L'hook è installato (simbolo giusto)? La cartella della mod è quella che Ryujinx carica (scheda Ryujinx)? Un'altra mod è disattivata? |
| Il gioco va in crash | Un puntatore è nullo o un offset è sbagliato. Aggiungi controlli **Is null?**; conferma gli offset per la versione 1.0.0. |
| Una scorciatoia non funziona | Strumenti > Scorciatoie da tastiera: potrebbe essere stata modificata. |
| La disposizione della finestra è strana | Visualizza: mostra il pannello di output (Ctrl+J); trascina i pannelli dove preferisci. |

Se segnali un problema, includi il registro **Build** (Salva il registro di compilazione).
