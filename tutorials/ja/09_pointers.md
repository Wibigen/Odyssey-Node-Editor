# ポインタとメモリ

ゲームのコードはポインタ(`al::LiveActor*`、`StageScene*`)だらけです。*ポインタとメモリ* ブロックは、C++ でそれらに行う操作をカバーします。

| ブロック | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | 変換 `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` または `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | *ベース + バイトオフセット* の値 |

## 典型的な流れ

1. フックがシーンなどの引数を渡します。
2. **Call by name** やゲーム関数がオブジェクトのポインタ(たとえばプレイヤー)を返します。
3. **Is null?** → Branch でクラッシュを防ぎます。
4. そのポインタに **Call method** や **Get member** を使います。

## 注意

オフセットとレイアウトは **バージョン 1.0.0** 向けの OdysseyDecomp に基づいています。ご自身のバージョンで確認してください。誤ったオフセットへの読み書きはゲームのクラッシュを招きます。
