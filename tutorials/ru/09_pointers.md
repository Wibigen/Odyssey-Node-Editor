# Указатели и память

Код игры полон указателей (`al::LiveActor*`, `StageScene*`). Блоки *Указатели и память* покрывают то, что C++ с ними делает.

| Блок | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | преобразование `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` или `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | значение по *базе + смещению в байтах* |

## Типичная схема

1. Хук даёт аргумент, например сцену.
2. **Call by name** / игровая функция возвращает указатель на объект (например, игрока).
3. **Is null?** → Branch, чтобы избежать краша.
4. **Call method** или **Get member** для него.

## Осторожно

Смещения и раскладки берутся из OdysseyDecomp для **версии 1.0.0**: проверьте их для своей версии. Чтение или запись по неверному смещению приводит к падению игры.
