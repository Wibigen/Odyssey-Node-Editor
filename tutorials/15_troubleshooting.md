# Troubleshooting

| Problem | What to try |
|---|---|
| *The function catalog is empty* | Tools > Settings: choose your OdysseyDecomp folder (with `data/file_list.yml`) and extract the catalog. |
| A function returns `void` but should not | Change the return type (see *Calling and hooking game functions*). |
| *Problems* tab lists something | Double-click a line: the node is selected. Usually an unconnected input or a missing variable. |
| Compile says it cannot find a header | Add it in the **Includes** tab, or fix your project's include folders. |
| The build folder is broken | Tools > **Repair exlaunch base**. |
| Nothing happens in game | Is the hook installed (right symbol)? Is the mod folder the one Ryujinx loads (Ryujinx tab)? Is another mod disabled? |
| The game crashes | A pointer is null or an offset is wrong. Add **Is null?** checks; confirm the offsets for version 1.0.0. |
| A shortcut does not work | Tools > Keyboard shortcuts: it may have been changed. |
| The window layout is odd | View: show the output panel (Ctrl+J); drag the docks back where you want them. |

If you report a problem, include the **Build** log (Save log as…).
