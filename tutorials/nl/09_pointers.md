# Pointers en geheugen

Spelcode zit vol pointers (`al::LiveActor*`, `StageScene*`). De blokken *Pointers en geheugen* dekken wat C++ ermee doet.

| Blok | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | conversie `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` of `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | de waarde op *basis + byte-offset* |

## Typisch patroon

1. Een hook geeft je een argument zoals de scène.
2. **Call by name** / een spelfunctie geeft een objectpointer terug (bijvoorbeeld de speler).
3. **Is null?** → Branch, om een crash te voorkomen.
4. **Call method** of **Get member** erop.

## Opgelet

Offsets en indelingen komen uit OdysseyDecomp voor **versie 1.0.0**: controleer ze voor jouw versie. Lezen of schrijven op een verkeerde offset laat het spel crashen.
