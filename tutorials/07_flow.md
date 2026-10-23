# Flow control

The **Flow** blocks decide *which* nodes run and *how often*.

| Block | What it does |
|---|---|
| **Branch (if / else)** | Condition **c**: runs the **then** path or the **else** path, then continues. |
| **Switch** | Picks a path from an integer value; edit the cases as small boxes with a **+** button. |
| **For loop** | Repeats a path N times; the index is an output. |
| **While loop** | Repeats while a condition is true. |
| **Return** | Leaves the current function or hook, optionally with a value. |

## Reading the flow

Follow the white arrows. A node with two arrow outputs (Branch) has two possible next steps; both can continue to a shared node afterwards.

## Tips

* Keep a loop short: hooks run on the game's main thread, every frame.
* To do something **once** per condition change, store the previous state in a **Global variable**.
* Wrap a repeated idea in your own function (next tutorial).
