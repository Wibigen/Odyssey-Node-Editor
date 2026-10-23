# Plugins

Plugins add **nodes**, **function catalogs**, **themes**, **templates** and **tutorials**.

## Plugin explorer

**Plugins > Plugin explorer** (Ctrl+Shift+P): every plugin with its picture, author, version and content. **Enable / Disable**, **Install…** (a `.zip` / `.odnp` or a folder), **Remove**, **New plugin…** (a skeleton to edit), **Show folder**.

Bundled: *Standard I/O*, *Strings*, *Extra themes* and **Dear ImGui** (off by default).

## Using what a plugin adds

* Nodes appear in the **Blocks** list under the plugin's categories, with a soft coloured glow on the canvas.
* A catalog opens with **Plugin function…** (Ctrl+Shift+K, or the button above the block list, or the menu on a released link).
* Templates: **File > New from template**.
* Tutorials: **Tutorials** window, *Plugin tutorials* section.

## Plugins that change your project

Some plugins (Dear ImGui) need files and CMake lines in your exlaunch project. The editor **offers** it when you enable them: nothing is overwritten, a backup of `CMakeLists.txt` is kept, and *Plugin explorer > Exlaunch base…* removes exactly what was added.

## Safety

A plugin with a `plugin.py` file runs Python with the same rights as the editor. Install plugins from people you trust.

## Writing one

See `PLUGINS.md` (format, node templates, themes, help pages, settings).
