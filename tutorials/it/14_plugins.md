# Plugin

I plugin aggiungono **nodi**, **cataloghi di funzioni**, **temi**, **modelli** e **tutorial**.

## Esplora plugin

**Plugin > Esplora plugin** (Ctrl+Maiusc+P): ogni plugin con la sua immagine, autore, versione e contenuto. **Attiva / Disattiva**, **Installa…** (un `.zip` / `.odnp` o una cartella), **Rimuovi**, **Nuovo plugin…** (uno scheletro da modificare), **Mostra cartella**.

Inclusi: *I/O standard*, *Stringhe*, *Temi aggiuntivi* e **Dear ImGui** (disattivato per impostazione predefinita).

## Usare ciò che un plugin aggiunge

* I nodi compaiono nell'elenco **Blocchi** sotto le categorie del plugin, con un morbido alone colorato sulla tela.
* Un catalogo si apre con **Funzione di plugin…** (Ctrl+Maiusc+K, il pulsante sopra l'elenco dei blocchi o il menu al rilascio di un collegamento).
* Modelli: **File > Nuovo da modello**.
* Tutorial: finestra **Tutorial**, sezione *Tutorial dei plugin*.

## Plugin che modificano il tuo progetto

Alcuni plugin (Dear ImGui) hanno bisogno di file e righe CMake nel tuo progetto exlaunch. L'editor te lo **propone** quando li attivi: nulla viene sovrascritto, viene conservato un backup di `CMakeLists.txt` e *Esplora plugin > Base exlaunch…* rimuove esattamente ciò che è stato aggiunto.

## Sicurezza

Un plugin con un file `plugin.py` esegue Python con gli stessi permessi dell'editor. Installa solo plugin di persone di cui ti fidi.

## Scriverne uno

Vedi `PLUGINS.md` (formato, modelli di nodi, temi, pagine di aiuto, impostazioni).
