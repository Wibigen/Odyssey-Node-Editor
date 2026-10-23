# Puntatori e memoria

Il codice del gioco è pieno di puntatori (`al::LiveActor*`, `StageScene*`). I blocchi *Puntatori e memoria* coprono ciò che il C++ fa con essi.

| Blocco | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | conversione `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` oppure `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | il valore a *base + offset in byte* |

## Schema tipico

1. Un hook ti dà un argomento come la scena.
2. **Call by name** / una funzione del gioco restituisce un puntatore a un oggetto (per esempio il giocatore).
3. **Is null?** → Branch, per evitare un arresto anomalo.
4. **Call method** o **Get member** su di esso.

## Attenzione

Offset e layout provengono da OdysseyDecomp per la **versione 1.0.0**: verificali per la tua versione. Leggere o scrivere a un offset sbagliato manda in crash il gioco.
