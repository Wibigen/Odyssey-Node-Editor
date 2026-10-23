# Odyssey Node Editor  (v7.7)

A native desktop tool (Python + PySide6, no browser) for building **Super Mario Odyssey 1.0.0 exefs mods** with Blueprint-style nodes.
It generates [exlaunch](https://github.com/shadowninja108/exlaunch) C++ that compiles against your OdysseyDecomp fork.

## Run
- Windows: double-click `run.bat` (installs PySide6 on first run). Or `pip install -r requirements.txt` then `python odyssey_nodes.py`.
- Standalone exe (optional): `build_exe.bat` builds `OdysseyNodes.exe` right next to the script (logo embedded) and removes `build/`, `dist/`, the `.spec` and `__pycache__` folders.

## First start
The setup dialog asks for your **OdysseyDecomp folder**. The tool reads `data/file_list.yml`, demangles the symbols (needs `c++filt`, found automatically or set in Settings) and builds the function catalog itself (about 17,700 functions). It also asks for your exlaunch project, `main.cpp` path and the build command (default `cmake --build build`).

## Learning the editor
- **Help > Tutorials…** (F1): 15 short tutorials (start here, project setup, your first mod, the canvas, game functions and hooks, variables and math, flow control, your own functions, pointers, custom code, groups and library, output and building, preferences and shortcuts, plugins, troubleshooting), then the tutorials of enabled plugins in a separate *Plugin tutorials* section. The pages are the Markdown files of `tutorials/` (list in `tutorials/index.json`).
- **Help > Interface tour…**: a guided presentation of the window. It starts the first time the program is opened; Skip / Esc ends it. Once completed or skipped it does not come back at startup (if you close the program in the middle it does).

## Files and languages
- **File > Save** (Ctrl+S) writes to the file you are editing; **Save as…** (Ctrl+Shift+S); **File > Open recent**. The window title shows the file name and a dot when there are unsaved changes.
- **View > Language** (globe icon): English (default), Français, Deutsch, Español, Italiano, Nederlands, Русский, 日本語, 中文. Applied after a restart. Packs are `lang/<code>.json` (`{"English text": "translation"}`); a copy in your data folder's `lang/` overrides or adds a language. Plugin content stays in English unless the plugin brings its own translations.

## Using it
- **Add game function** (Ctrl+F, the red button, or right-click on the canvas): a full window to search functions, see signature / return type / offset / symbol, then choose **Call** or **Hook**. For a call, every argument is either *Connect a node* or a *Fixed value* (number, text, bool, `Vector3` X/Y/Z, any C++ expression). The result can be saved in a variable, or used directly as a value in other blocks. A button next to each function opens it in a GitHub search of OdysseyDecomp. If the catalog says *void* for a function that really returns something, use **Change...** next to the return type (a warning asks you to confirm).
- Blocks: Flow (branch, switch, for, while, return), Variables (declare, set, get, global, constant), Functions (define / call), Math & logic, Pointers & memory (address-of, dereference, null check, cast, member get/set, **call method**, read/write at offset), Custom code. Function arguments and switch cases are edited as small boxes with a **+** button.
- A *Declare variable* block that is not inside a function becomes a global variable.
- **Groups and comments**: select nodes and press Ctrl+G to frame them (drag the title to move all), add comments with Ctrl+Shift+C, tidy up with Ctrl+L.
- **Import C++** (Ctrl+I): turns a `.cpp` into a graph, as far as it understands it; the rest is kept as custom code.
- **Library**: Library > Save selection to library stores a function (with everything it uses) or a template as a `.odnf` file in your data folder (`%APPDATA%\OdysseyNodes\library`). They appear in the block list and the Library menu and are inserted inside a group.
- **Inspector**: signature, return type, offset with the symbol under it, status, settings, inputs (wired or fixed), outputs, Duplicate / Disconnect / Delete, and *Edit this block...*.
- **Output panel**: C++ code (the lines of the selected node are highlighted), Includes, Problems, Build. Collapse it with the arrow, Ctrl+J, or by double-clicking a tab.
- **Repair base**: deletes the project's `build` folder and re-runs `cmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake`.
- **Ryujinx tab**: set the Ryujinx executable, game file and a mod folder name once (the data folder is detected, otherwise asked); then "Install mod and launch" copies `subsdkN` (number read from CMakeLists.txt) and `main.npdm` from the build folder (WSL included) into `<Ryujinx>/mods/contents/0100000000010000/<name>/exefs` and starts the game.
- Calls are plain C++ (`rs::getPlayerActor(scene)`); by-address calls are an option (Preferences > Advanced). Re-extract the catalog once to record static functions.
- Math & logic nodes are drawn as small squares. Groups can be edited (name, color, nodes). Favorites (☆) in the function browser. Clear the graph from the Edit menu.
- **Compile** (F5) runs your build command and shows the log. Choose where it runs in Settings: Windows (cmd), **WSL** (pick your distro, e.g. Ubuntu) or the native shell; the first Compile asks. Project folders like `\\wsl$\Ubuntu\home\me\proj` work. **Write to project** saves the C++ into `src/program/main.cpp` or `src/main.cpp` (whichever exists) of your exlaunch project.
- Graphs are saved as `.odn` (autosaved too); `.json` files from older versions can still be opened. File > Save as startup graph sets what File > New opens.
- **Preferences** (Ctrl+,): startup behaviour, autosave, grid, snapping, code font, text size.

Shortcuts: Ctrl+F browse, Ctrl+Z/Y undo/redo, Ctrl+D duplicate, Del delete, Ctrl+A select all, Ctrl+G group, Ctrl+Shift+C comment, Ctrl+L arrange, Ctrl+I import C++, F fit, Ctrl+J output, Ctrl+E write, F5 compile, Ctrl+S/O/N, Ctrl+, preferences.

## Layout
```
odyssey_nodes.py(.pyw)   entry point
assets/logo.png, logo.ico  application logo (window, taskbar, exe icon)
odyssey/app.py           startup, theme
odyssey/config.py        paths and settings (%APPDATA%/OdysseyNodes)
odyssey/catalog.py       file_list.yml -> catalog.json
odyssey/graph.py         node model, validation, C++ generation
odyssey/cppimport.py     C++ -> graph (best effort)
odyssey/library.py       saved functions (.odnf)
odyssey/layout.py        automatic arrangement
odyssey/rettype.py       return type override
odyssey/prefs_dialog.py, library_dialog.py
odyssey/canvas.py        node canvas
odyssey/widgets.py       palette, inspector, highlighter, build runner
odyssey/function_dialog.py  function browser / block builder
odyssey/valueedit.py     typed value editors
odyssey/mainwindow.py    main window
odyssey/setup_dialog.py, theme.py
```

## Limits (be honest)
- Developed and tested headless on Linux (offscreen Qt). Not yet run on Windows, nor against a real exlaunch build or a Switch.
- Generated code was syntax-checked with clang against the decomp headers and a stub `exlaunch.hpp`, not linked.
- Offsets come from `file_list.yml`; verify them for your game version. Return types and class-vs-namespace are guessed from headers.
- No type check between wired pointer types yet (e.g. `StageScene*` into `al::LiveActor*` is a C++ error you will see at build time).
- C++ import is heuristic: it understands the code this tool generates and common hand-written patterns; templates, classes, macros other than the hook macro and fall-through switches stay as custom code.
- The catalog guesses return types from headers (ambiguous names default to void); check them in the decompiled source.
- No latent nodes (delay/sequence) or actor-spawn pools yet. A local declared inside a branch is scoped to that branch.

## Credits
- [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) by MonsterDruide1 and contributors (symbol and offset data, headers)
- [exlaunch](https://github.com/shadowninja108/exlaunch) by shadowninja108 (hook framework targeted by the generated code)
- [SMO-Exlaunch-Base](https://github.com/CraftyBoss/SMO-Exlaunch-Base) by CraftyBoss (GPL-2.0): the ImGui backend for Switch / nvn used by the Dear ImGui plugin; based on [LunaKit](https://github.com/Amethyst-szs/smo-lunakit) by Amethyst-szs (GPL-2.0) and [exlaunch-cmake](https://github.com/EngineLessCC/exlaunch-cmake)
- [Dear ImGui](https://github.com/ocornut/imgui) by Omar Cornut (MIT)
- [sead](https://github.com/open-ead/sead) and [nnheaders](https://github.com/open-ead/nnheaders) by open-ead
- [PySide6 / Qt](https://www.qt.io/qt-for-python), PyInstaller
- Inspired by Unreal Engine Blueprints

## Plugins and shortcuts (v6)
* **Plugins > Plugin explorer** manages plugins (nodes, themes, menu commands). Bundled: Standard I/O, Strings, Extra themes. Format and examples: `PLUGINS.md`.
* **Tools > Keyboard shortcuts** changes any shortcut (stored in your settings).

## Dear ImGui plugin (v7)
* The bundled **Dear ImGui** plugin is **disabled by default**: enable it in Plugins > Plugin explorer. It adds ~350 ImGui functions, 41 `ImDrawList` methods and ~500 constants (flags, colours, keys...) as nodes, plus *Add draw function* and a few helpers (ImVec2, ImVec4, IM_COL32, flags OR, address of).
* **Edit > Add plugin function** (Ctrl+Shift+K, or the button in the block palette) opens the **plugin function browser**: search, categories, signature and description, "keep open to add several".
* Functions that return a value (Button, Checkbox, Begin...) can be used as a statement or, with right-click > *Use as a value*, directly inside another node.
* When you enable the plugin (or load its template, or write a graph that uses it) the editor offers to **add ImGui to your exlaunch project**: missing support files are copied (nothing is overwritten, files you already have are left alone), one marked block is appended to `CMakeLists.txt` (backup `CMakeLists.txt.odn-backup`). Plugin explorer > *Exlaunch base...* shows the state and removes exactly what was added.
* **Help > Tutorials > Plugin tutorials > How to use Dear ImGui**: a tutorial (quick start, how a draw function works, finding nodes, pointers and text, recipes, in-game controls, troubleshooting) with buttons that load the example, open the function browser or the project base. Any plugin can ship help pages (see PLUGINS.md); they are listed in *Help > Tutorials…* (F1) while the plugin is enabled.
* **Tested base layout**: [Fuzzy2319/SMO-Exlaunch-Base](https://github.com/Fuzzy2319/SMO-Exlaunch-Base), i.e. exlaunch + [OdysseyHeaders](https://github.com/MonsterDruide1/OdysseyHeaders) in `include/`. The patch uses the nn / sead / nvn headers your project already has and adds only what is missing (glslc, `nvn_CppFuncPtrImpl.h`, the backend in `src/`). The code was adapted by hand-testing a build on such a base with devkitA64; this editor itself never compiles for the Switch.
* **File > New from template > Hello ImGui** loads a ready graph: it draws a window with a text and a button that counts presses. In the game, ZL + ZR (changeable in Exlaunch base… > Gamepad) gives the controller to ImGui while a window is shown (mouse and keyboard always work; touch only when your SDK headers declare it).
* Not compiled here: the code and the patch were checked by generating / simulating on a copy of the base, not by a real Switch build. If your build fails, copy the log.
