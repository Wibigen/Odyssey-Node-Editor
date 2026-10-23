# The canvas: nodes, pins and links

## Nodes and pins

A node has **input pins** on the left and **output pins** on the right.

* **White arrow pins** are the **order of execution**: the node runs after the one wired to its *in* pin, then continues through *next*.
* **Coloured circles** are **values**. The colour depends on the type (number, pointer, bool, text…). A filled circle is wired; an empty one is free.
* An input that is not wired shows a **fixed value** you type in the inspector (`= 60`).

## Linking

* **Drag from a pin to another pin** (an output to an input).
* A value output can feed **several** inputs; an execution output goes to **one** next node.
* **Release on empty space**: a menu offers *Game function…*, *Plugin function…* (when a plugin has a catalog) and all the blocks that fit; the new node is created and connected for you. (Turn it off in Preferences.)
* Select a node and press **Delete** to remove it; *Inspector > Disconnect* removes only its links.

## Moving around

| Action | How |
|---|---|
| Zoom | Mouse wheel (Ctrl +/-) |
| Pan | Hold the **middle button** and drag |
| Fit everything | **F** |
| Select several | Drag a rectangle on empty space; Ctrl+A for all |
| Duplicate / delete | Ctrl+D / Del |
| Undo / redo | Ctrl+Z / Ctrl+Y |
| Find a node | Ctrl+F in the graph (the search icon) |
| Tidy up | Ctrl+L arranges the nodes automatically |

## Adding blocks

* **Double-click** or **drag** a block from the **Blocks** list.
* **Right-click** the empty canvas for the same choices, plus *Comment here*.
* The filter box above the list searches names and descriptions.

## Colours

Each kind of node has its own header colour. Nodes that come from a **plugin** also have a soft glow in the plugin's colour, so you can tell them apart at a glance.
