# La tua prima mod

Obiettivo: eseguire qualcosa **una volta al secondo** durante il gioco. Il grafo di esempio lo fa; qui lo costruisci tu stesso per conoscere ogni parte.

## 1. Agganciare una funzione del gioco

1. Fai clic su **Funzione del gioco…** (pulsante rosso, oppure Ctrl+Maiusc+F).
2. Cerca `exePlay` e seleziona **StageScene::exePlay** (viene eseguita a ogni fotogramma mentre giochi).
3. Scegli **Aggancia questa funzione**, lascia la modalità *Esegui prima l'originale, poi il mio grafo* e premi **Aggiungi al grafo**.

Compare un nodo rosso **Hook StageScene::exePlay**. Il suo pin bianco **next** è il punto da cui parte la tua logica.

## 2. Contare i fotogrammi

1. Aggiungi una **Variabile globale** (Variabili): tipo `int`, nome `frames`, valore iniziale `0`. Una globale mantiene il suo valore da un fotogramma al successivo.
2. Aggiungi **Set variable**, scegli `frames` e collega **hook next → in**.
3. Aggiungi **Get variable** `frames` e **Math (A + B)** di tipo `int`, B = `1`; collega *Get → A*, *Math out → Set v*.

## 3. Fare qualcosa ogni 60 fotogrammi

1. Aggiungi **Branch (if / else)** dopo il Set variable.
2. Condizione: **Compare** `(frames % 60) == 0` (un nodo *Math* con `%` e 60 che alimenta un *Compare* con `== 0`). Collega il risultato al pin **c** del Branch.
3. Metti ciò che vuoi sul percorso **then**, per esempio una **Custom statement** `/* il mio codice qui */`, oppure una chiamata a una funzione del gioco.

## 4. Guardare il codice

Apri la scheda **Codice C++**: ci sono l'hook, la variabile e l'`if`. Seleziona un nodo: le sue righe vengono evidenziate.

## 5. Compilare e provare

1. La scheda **Problemi** è vuota? Bene.
2. **Scrivi nel progetto** (Ctrl+E), poi **Compila** (F5).
3. Scheda **Ryujinx** > *Installa la mod e avvia*.

> Partenza più rapida: **File > Nuovo da modello** (o il grafo di esempio in Preferenze > Apri con) ti dà un grafo già pronto.
