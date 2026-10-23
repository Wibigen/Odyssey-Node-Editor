# Pointers and memory

Game code is full of pointers (`al::LiveActor*`, `StageScene*`). The *Pointers & memory* blocks cover what C++ does with them.

| Block | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | `(Type)value` conversion |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` or `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | the value at *base + byte offset* |

## Typical pattern

1. A hook gives you an argument such as the scene.
2. **Call by name** / a game function returns an object pointer (for example the player).
3. **Is null?** → Branch, to avoid crashing.
4. **Call method** or **Get member** on it.

## Careful

Offsets and layouts come from OdysseyDecomp for **version 1.0.0**: check them for your version. Reading or writing the wrong offset crashes the game.
