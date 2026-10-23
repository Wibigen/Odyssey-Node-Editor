# Plugins

Plugins add nodes, themes and menu commands to Odyssey Node Editor. Open **Plugins > Plugin explorer** (Ctrl+Shift+P) to see, enable, disable, install, remove or create plugins.

* Bundled plugins live in `plugins/` next to the program (they can be disabled, not removed).
* Installed plugins live in your user folder (Plugins > Open the plugins folder): `%APPDATA%/OdysseyNodes/plugins/` on Windows, `~/.config/OdysseyNodes/plugins/` elsewhere.
* A plugin with the same id as a bundled one replaces it.
* Share a plugin as a `.zip` / `.odnp` file (a zip of the plugin folder) and install it with **Install > From an archive**.

## Help pages
A plugin can ship Markdown help pages, shown in the **Tutorials** window (*Help > Tutorials…*, F1), in its *Plugin tutorials* section (after the editor's own tutorials), while it is enabled:

```json
"help": [{"title": "How to use my plugin", "file": "help/using.md",
          "buttons": [{"label": "Load the example", "do": "template:My template"}]}]
```

Without the key, every `help/*.md` file is a page. Button actions (`do`): `template:<template name>`, `base:<plugin id>` (the exlaunch base dialog), `browser:<plugin id>` (the function browser), `plugins` (the explorer), `tour` (the interface tour), `settings`. Standard Markdown: headings, lists, tables, code blocks, links (http / https open in the browser).

## Folder layout

```
my-plugin/
  plugin.json      information + nodes + themes   (everything optional)
  icon.png         square picture (any size, cropped to a square)
  nodes.json       more nodes: a list              (optional)
  nodes/*.json     one node or a list per file     (optional)
  plugin.py        Python code with register(api)  (optional, see below)
  functions.json   function catalog (optional, "catalog" in plugin.json)
  templates/*.odn  graphs for File > New from template (optional)
  base/            files copied into the exlaunch project (optional, "base" in plugin.json)
```

### plugin.json

```json
{
  "id": "my-plugin",
  "title": "My plugin",
  "author": "You",
  "version": "1.0.0",
  "description": "What it adds.",
  "icon": "icon.png",
  "color": "#c98a2b",
  "default_enabled": true,
  "nodes": [ ... ],
  "themes": [ ... ]
}
```

Missing information gets a default: title = folder name, author = "Unknown author", version = "0.0.0", description = "No description provided.", picture = a colored square with the first letter of the title.

## Nodes

```json
{
  "id": "printf",
  "label": "Print (printf)",
  "category": "Standard I/O",
  "description": "Shown as a tooltip in the block list.",
  "flow": true,
  "inputs": [ {"id": "format", "type": "const char*", "label": "format", "default": "\"hello\\n\""} ],
  "repeat": {"id": "arg", "type": "", "label": "argument", "min": 0, "max": 6, "default": 0},
  "output": {"type": "int", "label": "result"},
  "fields": [ {"key": "mode", "label": "Mode", "kind": "choice", "options": [["a", "Alpha"], ["b", "Beta"]], "default": "a"} ],
  "template": "printf($format$,arg)",
  "includes": ["<cstdio>"],
  "helpers": "static int helper() { return 1; }",
  "color": "#2fa66a"
}
```

| key | meaning |
|---|---|
| `flow` | `true`: a statement with execution pins (it is placed in a chain of nodes). `false` / absent: a value you plug into other nodes. |
| `inputs` | typed input pins. `type` is a C++ type (empty = any). `default` is the C++ text used when nothing is connected (empty = a neutral value). |
| `repeat` | optional list of extra inputs `arg1, arg2...`; the number is chosen in the inspector. |
| `output` | the value pin. Value nodes have one by default. A flow node can have one too: its result is kept in a variable (`Save result as` in the inspector). |
| `fields` | settings shown in the inspector. Kinds: `text`, `type`, `bool`, `choice` (with `options`). |
| `includes` | `#include` lines added to the generated file (`"<cstdio>"`, `"\"my.h\""`, or a bare name = `<name>`). |
| `helpers` | C++ code added once before your functions. |

Template: `@key` = value of a field, `$id` = what is plugged into an input, `$,arg` = the repeated inputs as `, a, b` (nothing when there are none), `$*arg` = `a, b`. A flow node without output is written as a statement; with an output it becomes `type name = template;`.

A graph keeps a copy of the definition of the plugin nodes it uses, so it still opens and generates the same code when the plugin is disabled or missing (a warning appears in Problems).

## Themes

```json
"themes": [ {"id": "midnight", "name": "Midnight", "base": "dark", "accent": "#5b8def",
             "colors": {"bg": "#0b0f1a", "node": "#151b2b"}} ]
```

`base` is `dark` or `light`; `colors` only lists what changes. Keys: bg, bg2, pn, node, ln, grid, tx, mu, ok, ko, val, warn, sub, bar, code_num, code_kw, code_pp, code_str, code_cm. Themes appear in View > Theme and Preferences. Choose Accent color > "Theme default" to use the theme's own accent.

## Python (optional)

`plugin.py` runs when the plugin is loaded (only install Python plugins from people you trust: they run with your rights):

```python
def register(api):
    api.add_node({"id": "hello", "template": "printf(\"hi\\n\")", "flow": True})
    api.add_theme("neon", "Neon", base="dark", colors={"bg": "#05060a"}, accent="#00e5ff")
    api.add_action("Show graph size", lambda w: w.statusBar().showMessage(f"{len(w.graph.nodes)} nodes", 4000), shortcut="Ctrl+Alt+G")
    # api.window (the main window), api.data (a dict saved in your settings), api.log("text")
```

Actions appear in the Plugins menu and in Tools > Keyboard shortcuts, where their shortcut can be changed.

## Node options added in v7

| key | meaning |
|---|---|
| `"both": true` | a statement (with execution pins) that gives a result and can also be used as a value: right-click the node > *Use as a value*. |
| `"place": "main"` | the node has no pins: its code is emitted once inside `exl_main`, before the hooks are installed (nodes are emitted top to bottom, then left to right). |
| `"init": ["Foo::Install();"]` | lines emitted once in `exl_main` whenever the node is used (identical lines are written once). |
| field kind `"func"` / `"var"` | the box offers the functions / variables of the graph. |

## Function catalogs

A catalog is a big list of functions that are not loaded as individual nodes: they are built when you add them (Edit > Add plugin function, Ctrl+Shift+K). Put `functions.json` (or `catalog.json`) in the plugin, or set `"catalog": "file.json"`.

```json
{
  "title": "Dear ImGui", "color": "#4a8fd9", "includes": ["\"imgui.h\""],
  "entries": [
    {"id": "Button", "label": "Button", "call": "ImGui::Button", "kind": "f", "r": "bool",
     "p": [["const char*", "label", ""], ["ImVec2", "size", "ImVec2(0, 0)"]],
     "c": "Widgets: Main", "d": "button", "va": false}
  ]
}
```

* `kind`: `f` function `call(args)`, `m` method `$self->call(args)` (adds an "object" input of type `self`), `c` constant (a value, `r` = its type).
* `p`: `[type, name, default]`; the default fills the pin when nothing is plugged in (text pins default to `""`).
* `va: true`: variable arguments (`...`), the number of extra arguments is set in the inspector.
* Functions with a result are *both*-nodes (see above). In graphs the node id is `plugin:entry`.

## Templates

`templates/*.odn` (or `"templates": [{"name": "...", "file": "templates/x.odn", "description": "..."}]` in plugin.json) are graphs saved from the editor. They appear in **File > New from template** while the plugin is enabled.

## Base patch (changing the exlaunch project)

```json
"base": {
  "title": "Dear ImGui on the exlaunch base", "payload": "base", "exact": ["imgui/"],
  "cmake": {"target": "auto",
            "definitions": ["IMGUI_USER_CONFIG=\"imgui_backend/nvn_imgui_config.h\""],
            "include_dirs": ["imgui", "src", "src/program"],
            "glob_sources": ["imgui/*.cpp"], "embed": ["romfs/ShaderData/imgui.bin"]}}
```

* Every file of `base/` is copied into the project **only if the project does not have it** (matched by its last two path parts, e.g. `nn/hid.h`; paths starting with an `exact` prefix must match exactly). Nothing is overwritten.
* `CMakeLists.txt` gets one marked block with only the pieces it lacks; the first time a backup `CMakeLists.txt.odn-backup` is kept.
* `base.settings` (optional) adds choices to the base dialog and writes them into one generated header:
  `"settings": {"title": "Gamepad", "file": "src/odn_imgui_config.h", "template": "#define MODE $mode\n", "fields": [{"id": "mode", "label": "Mode", "default": "1", "options": [["1", "Combo"], ["2", "Auto"]], "enabled_if": {"other": "1"}}]}`.
  Each field is a list of `[value, label]` options; `$id` in the template is replaced by the chosen value (only listed values are accepted); `enabled_if` greys a field unless the other fields have the given values. The file is rewritten when a choice changes and removed by *Remove*.
* `<project>/.odn/base_<plugin>.json` records what was added, so *Remove* takes back exactly that (files you edited since are kept).
* The editor offers the patch when the plugin is enabled, when one of its templates is loaded and before writing a graph that uses it.

## Translating a plugin
The editor's own texts are translated by `lang/<code>.json`. Plugin names, node titles and help pages are not: they show as you wrote them. To offer help pages in other languages, put them in `help/<code>/` (for example `help/fr/using_imgui.md`); the editor opens the page of the interface language and falls back to the file next to it (English).
