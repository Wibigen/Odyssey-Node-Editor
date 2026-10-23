# Zeiger und Speicher

Spielcode ist voller Zeiger (`al::LiveActor*`, `StageScene*`). Die Blöcke *Zeiger und Speicher* decken ab, was C++ mit ihnen macht.

| Block | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | Umwandlung `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` oder `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | der Wert bei *Basis + Byte-Offset* |

## Typisches Muster

1. Ein Hook liefert Ihnen ein Argument wie die Szene.
2. **Call by name** / eine Spielfunktion gibt einen Objektzeiger zurück (zum Beispiel den Spieler).
3. **Is null?** → Branch, um Abstürze zu vermeiden.
4. **Call method** oder **Get member** darauf.

## Vorsicht

Offsets und Layouts stammen aus OdysseyDecomp für **Version 1.0.0**: Prüfen Sie sie für Ihre Version. Das Lesen oder Schreiben an einem falschen Offset bringt das Spiel zum Absturz.
