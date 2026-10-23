# Codice personalizzato e importazione di C++

I nodi coprono molto, non tutto. Due vie d'uscita ti permettono di andare avanti.

## Blocchi personalizzati

* **Custom expression**: qualsiasi espressione C++ usata come valore.
* **Custom statement**: qualsiasi istruzione C++ nel flusso.

Collega fino a otto ingressi e indicali come `$a` … `$h` nel tuo testo:

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## File di inclusione

La scheda **Includes** (in basso) elenca le righe `#include` del file generato. Aggiungi gli header di cui il tuo codice personalizzato ha bisogno.

## Importare C++

**File > Importa file C++…** (Ctrl+I) trasforma un `.cpp` in un grafo per quanto lo capisce. Legge il codice scritto da questo strumento e gli schemi comuni scritti a mano; template, classi e macro insolite restano codice personalizzato. Controlla poi la scheda *Problemi*.
