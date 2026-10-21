# Odyssey Nodes  (v1.2)

A native desktop tool (Python + PySide6, no browser) for building **Super Mario Odyssey 1.0.0 exefs mods** with Blueprint-style nodes.
It generates [exlaunch](https://github.com/shadowninja108/exlaunch) C++ that compiles against your OdysseyDecomp fork.

## Run
- Windows: double-click `run.bat` (installs PySide6 on first run). Or `pip install -r requirements.txt` then `python odyssey_nodes.py`.
- Standalone exe (optional): `build_exe.bat` builds `OdysseyNodes.exe` right next to the script (logo embedded) and removes `build/`, `dist/`, the `.spec` and `__pycache__` folders.

## First start
The setup dialog asks for your **OdysseyDecomp folder**. The tool reads `data/file_list.yml`, demangles the symbols (needs `c++filt`, found automatically or set in Settings) and builds the function catalog itself (about 17,700 functions). It also asks for your exlaunch project, `main.cpp` path and the build command (default `cmake --build build`).

## Using it
- **Add game function** (Ctrl+F, the red button, or right-click on the canvas): a full window to search functions, see signature / return type / offset / symbol, then choose **Call** or **Hook**. For a call, every argument is either *Connect a node* or a *Fixed value* (number, text, bool, `Vector3` X/Y/Z, any C++ expression), and the result can be saved in a named variable.
- Blocks: Flow (branch, switch, for, while, return), Variables (declare, set, get, global, constant), Functions (define / call), Math & logic, Pointers & memory (address-of, dereference, null check, cast, member get/set, read/write at offset), Custom code.
- Inputs of any block can hold a typed fixed value instead of a wire; the value is shown on the node.
- **Inspector**: signature, return type, offset with the symbol under it, status, settings, inputs (wired or fixed), outputs, Duplicate / Disconnect / Delete, and *Edit this block...*.
- **Output panel**: C++ code, Includes, Problems, Build. Collapse it with the arrow, Ctrl+J, or by double-clicking a tab.
- **Compile** (F5) runs your build command and shows the log. Choose where it runs in Settings: Windows (cmd), **WSL** (pick your distro, e.g. Ubuntu) or the native shell; the first Compile asks. Project folders like `\\wsl$\Ubuntu\home\me\proj` work; **Write to project** saves the C++ into your `main.cpp`.
- Graphs are saved as `.odn` (autosaved too). Undo/redo, duplicate, zoom/pan, fit view.

Shortcuts: Ctrl+F browse, Ctrl+Z/Y undo/redo, Ctrl+D duplicate, Del delete, Ctrl+A select all, F fit, Ctrl+J output, Ctrl+E write, F5 compile, Ctrl+S/O/N.

## Layout
```
odyssey_nodes.py(.pyw)   entry point
assets/logo.png, logo.ico  application logo (window, taskbar, exe icon)
odyssey/app.py           startup, theme
odyssey/config.py        paths and settings (%APPDATA%/OdysseyNodes)
odyssey/catalog.py       file_list.yml -> catalog.json
odyssey/graph.py         node model, validation, C++ generation
odyssey/canvas.py        node canvas
odyssey/widgets.py       palette, inspector, highlighter, build runner
odyssey/function_dialog.py  function browser / block builder
odyssey/valueedit.py     typed value editors
odyssey/mainwindow.py    main window
odyssey/setup_dialog.py, theme.py
```

## Limits (be honest)
- Developed and tested headless on Linux (offscreen Qt). Not yet run on Windows, nor against a real exlaunch build or a Switch.
- Generated code was syntax-checked with clang against the decomp headers and a stub `lib.hpp`, not linked.
- Offsets come from `file_list.yml`; verify them for your game version. Return types and class-vs-namespace are guessed from headers.
- No type check between wired pointer types yet (e.g. `StageScene*` into `al::LiveActor*` is a C++ error you will see at build time).
- No latent nodes (delay/sequence) or actor-spawn pools yet. A local declared inside a branch is scoped to that branch.

## Credits
- [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) by MonsterDruide1 and contributors (symbol and offset data, headers)
- [exlaunch](https://github.com/shadowninja108/exlaunch) by shadowninja108 (hook framework targeted by the generated code)
- [sead](https://github.com/open-ead/sead) and [nnheaders](https://github.com/open-ead/nnheaders) by open-ead
- [PySide6 / Qt](https://www.qt.io/qt-for-python), PyInstaller
- Inspired by Unreal Engine Blueprints
