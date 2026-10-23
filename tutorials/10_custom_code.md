# Custom code and importing C++

Nodes cover a lot, not everything. Two escape hatches keep you moving.

## Custom blocks

* **Custom expression**: any C++ expression used as a value.
* **Custom statement**: any C++ statement in the flow.

Wire up to eight inputs and refer to them as `$a` … `$h` in your text:

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## Include files

The **Includes** tab (bottom) lists the `#include` lines of the generated file. Add the headers your custom code needs.

## Import C++

**File > Import C++ file…** (Ctrl+I) turns a `.cpp` into a graph as far as it understands it. It reads the code this tool writes and common hand-written patterns; templates, classes and unusual macros are kept as custom code. Check the *Problems* tab afterwards.
