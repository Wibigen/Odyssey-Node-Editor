# Punteros y memoria

El código del juego está lleno de punteros (`al::LiveActor*`, `StageScene*`). Los bloques *Punteros y memoria* cubren lo que C++ hace con ellos.

| Bloque | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | conversión `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` o `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | el valor en *base + desplazamiento en bytes* |

## Patrón típico

1. Un hook te da un argumento como la escena.
2. **Call by name** / una función del juego devuelve un puntero a un objeto (por ejemplo el jugador).
3. **Is null?** → Branch, para evitar un cierre inesperado.
4. **Call method** o **Get member** sobre él.

## Cuidado

Los offsets y las estructuras vienen de OdysseyDecomp para la **versión 1.0.0**: compruébalos para tu versión. Leer o escribir en un offset equivocado cierra el juego.
