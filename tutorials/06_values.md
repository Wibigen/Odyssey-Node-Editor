# Variables, values and math

## Variables (category *Variables*)

| Block | Use |
|---|---|
| **Declare variable** | A local variable (type, name, optional initial value). Lives in the flow where you declare it. |
| **Set variable** | Assign a new value. |
| **Get variable** | Read the current value (a value output, no execution pin). |
| **Global variable** | Keeps its value between frames and calls. A *Declare variable* that is not inside a function also becomes a global. |
| **Constant (value)** | A fixed number, text, bool or any C++ value you type. |

Use **Advanced** in the inspector for qualifiers (`static`, `const`…) and arrays (size and contents).

> A local declared inside a branch only exists in that branch (like in C++).

## Math & logic

Drawn as small squares:

* **Math (A + B)**: `+ - * / %` on two values (choose the type).
* **Compare**: `== != < > <= >=`, gives a bool.
* **Logic**: AND / OR; **NOT** inverts a bool.

Connect the result to a **Branch**'s condition, a variable, or an argument of a call.

## Fixed value or wire?

Any input pin can be **wired** to a node or given a **fixed value** (type it in the inspector). A wired input hides its fixed value.

## Types

Pin colours show types; the editor does not check pointer types between wires (for example `StageScene*` into `al::LiveActor*` is a C++ error you will see at build time). Use **Cast** (Pointers & memory) when you need to convert.
