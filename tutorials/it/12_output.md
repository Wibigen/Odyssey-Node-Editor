# Codice, problemi e compilazione

Il pannello **Output** in basso ha cinque schede. Comprimilo con la freccia, con **Ctrl+J** o con un doppio clic su una scheda.

## Codice C++

Anteprima in tempo reale del file generato. Le righe del **nodo selezionato** sono evidenziate. **Copia** e **Salva con nome…** lo esportano.

## Includes

Gli header all'inizio del file (vedi *Codice personalizzato*).

## Problemi

Ciò che manca o non va **prima** di compilare: ingressi non collegati, variabili sconosciute, hook vuoti. Fai doppio clic su una riga per andare al nodo.

## Build

* **Scrivi nel progetto** (Ctrl+E) salva il codice nel tuo progetto exlaunch.
* **Compila** (F5) esegue il comando di build e mostra l'output. **Copia errori** copia solo le righe di errore; **Salva il registro di compilazione** conserva l'intera console.
* **Ripara base** (menu Strumenti) elimina `build/` e riesegue CMake.

## Ryujinx

Imposta una volta sola l'emulatore, il file del gioco e un nome per la mod. **Installa la mod e avvia** copia `subsdkN` e `main.npdm` dalla tua cartella di build nella cartella delle mod di Ryujinx e avvia il gioco. Le opzioni includono compilare prima, disattivare le altre mod e lo schermo intero.

## Importante

L'editor stesso non compila mai per la Switch: lo fa la toolchain del tuo progetto. Se una build fallisce, copia il registro (indica esattamente quale file e quale riga).
