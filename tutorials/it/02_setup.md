# Configura il tuo progetto

Apri **Strumenti > Impostazioni** (Ctrl+Maiusc+,). Si apre da sola la prima volta.

## 1. La cartella di OdysseyDecomp

Scegli la cartella della tua copia di [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) (quella che contiene `data/file_list.yml`). L'editor costruisce allora il **catalogo delle funzioni** (circa 17.700 funzioni): nomi, argomenti, tipi di ritorno, offset e simboli. Si fa una volta sola e viene salvato. Serve lo strumento `c++filt` per leggere i nomi decorati; viene trovato automaticamente, oppure lo indichi nella stessa finestra.

Se il catalogo dice `void` per una funzione che in realtà restituisce qualcosa, puoi correggerlo più tardi (vedi *Chiamare e agganciare funzioni del gioco*).

## 2. Il tuo progetto exlaunch

* **Cartella del progetto**: la radice del tuo progetto exlaunch (quella con `CMakeLists.txt`). I percorsi Windows, `\\wsl$\Ubuntu\home\me\proj` e i percorsi WSL vengono compresi.
* **File generato**: dove viene scritto il codice. Vuoto = `src/program/main.cpp` oppure `src/main.cpp`, a seconda di quale esiste.

## 3. Il comando di build

Predefinito: `cmake --build build`. Scegli dove viene eseguito: **Windows (cmd)**, **WSL** (scegli la distribuzione, per esempio Ubuntu) o la shell nativa. Il primo *Compila* lo chiede se non è impostato.

## 4. Provalo

Apri la scheda **Ryujinx** (in basso) e imposta una volta sola l'eseguibile di Ryujinx, il file del gioco e un nome per la mod. *Installa la mod e avvia* copia la tua build nella cartella delle mod di Ryujinx e avvia il gioco.

## Se qualcosa non viene trovato

* Scheda **Problemi**: ciò che serve ancora al grafo.
* **Strumenti > Ripara la base exlaunch**: elimina la cartella `build` e riesegue CMake (ripara una configurazione danneggiata).
* Le Impostazioni si possono riaprire in qualsiasi momento; non si perde nulla.
