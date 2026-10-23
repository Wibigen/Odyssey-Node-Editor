# Calling and hooking game functions

Click **Game function…** (Ctrl+Shift+F) to search the catalog of Super Mario Odyssey functions.

## The browser

* Type part of a name, class or description. Categories on the left narrow the list.
* Select a function to see its **signature, return type, offset and symbol**.
* The star ☆ marks **favorites**; **Open on GitHub** opens a search for it in OdysseyDecomp (useful to read what it really does).

## Call or Hook?

| | **Call this function from my mod** | **Hook this function** |
|---|---|---|
| Meaning | *My graph calls this game function* | *When the game calls it, my graph runs* |
| Node | A node inside your flow | A red entry node (no input) |
| Typical use | `al::setPos(actor, …)`, `kill`, read a value | Run your code every frame, on a hit, on a pickup |

### Arguments of a call

Every argument is either **Connect a node** (wire a value in) or a **Fixed value**: a number, text, bool, a `Vector3` (X/Y/Z fields) or any C++ expression.

### Result

A call that returns a value can **save it in a variable** (name it in the inspector) or be used **directly as a value** inside another node (*Use as a value* in the inspector or right-click menu).

## Hook modes

| Mode | What runs |
|---|---|
| **Run the original first, then my graph** | The game function, then your logic (default). |
| **Run my graph first, then the original** | Your logic, then the game's. |
| **Replace the original** | Only your graph. |
| **Manual** | You place **Call original (Orig)** nodes where you want inside your graph. |

In *before* mode with a return value, an **original result** output gives you what the game returned. Change the return type or argument names in the inspector if needed.

## Wrong return type?

The catalog guesses return types from headers. If a function says `void` but returns something, use **Change…** next to the return type (a warning asks you to confirm). The choice is remembered.

## Call by name

For something that is not in the catalog, use **Call by name** (Functions): any C++ function written by name, e.g. `sead::Mathf::sqrt(x)`. **Get scene object** covers `al::getSceneObj<T>(…)`.

## Call style

*Preferences > Advanced*: calls are plain C++ by default (`rs::getPlayerActor(scene)`), or by address. A single node can override it (*Call style* in the inspector). Hooks install **by symbol** by default; the offset form is the fallback.
