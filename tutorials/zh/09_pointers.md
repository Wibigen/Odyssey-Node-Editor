# 指针与内存

游戏代码里到处都是指针(`al::LiveActor*`、`StageScene*`)。*指针与内存* 块涵盖了 C++ 对它们所做的操作。

| 块 | C++ |
|---|---|
| **Address of (&)** | `&value` |
| **Dereference (\*)** | `*ptr` |
| **Is null?** | `ptr == nullptr` |
| **Cast** | 转换 `(Type)value` |
| **Get member (->)** | `obj->field` |
| **Set member (->)** | `obj->field = v` |
| **Call method (->)** | `actor->kill()` |
| **Construct** | `Type(args)` 或 `new Type(args)` |
| **Array element** / **Set array element** | `a[i]` / `a[i] = v` |
| **Read at offset** / **Write at offset** | *基址 + 字节偏移* 处的值 |

## 典型模式

1. 钩子提供一个参数,例如场景。
2. **Call by name** / 游戏函数返回一个对象指针(例如玩家)。
3. **Is null?** → Branch,避免崩溃。
4. 对它使用 **Call method** 或 **Get member**。

## 注意

偏移和布局来自 OdysseyDecomp 的 **1.0.0 版本**:请针对你的版本确认。读写错误的偏移会使游戏崩溃。
