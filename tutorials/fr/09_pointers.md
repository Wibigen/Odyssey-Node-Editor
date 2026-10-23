# Pointeurs et mémoire

Le code du jeu est plein de pointeurs (`al::LiveActor*`, `StageScene*`). Les blocs *Pointeurs et mémoire* couvrent ce que le C++ fait avec eux.

| Bloc | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | conversion `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` ou `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | la valeur à *base + décalage en octets* |

## Schéma typique

1. Un hook vous donne un argument comme la scène.
2. **Call by name** / une fonction du jeu renvoie un pointeur d'objet (par exemple le joueur).
3. **Is null?** → Branch, pour éviter un plantage.
4. **Call method** ou **Get member** dessus.

## Attention

Les offsets et les structures viennent d'OdysseyDecomp pour la **version 1.0.0** : vérifiez-les pour votre version. Lire ou écrire au mauvais offset fait planter le jeu.
