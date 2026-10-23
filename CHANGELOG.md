# Changelog
Versioning: +1 for a big update, +0.1 for a small one.

## v7.6
- **Fix: the menu of a link released on empty space had no plugin function.** It now has **Plugin function…** next to *Game function…* (opens the plugin function browser; the chosen node is created and connected). Plugin node blocks were already in the categories.
- **Plugin nodes are easier to recognise:** a soft halo and a thin edge in the plugin's colour around the node (selected nodes keep the accent border).
- **Tutorials:** *Help topics* is now **Tutorials**. The plugin pages are no longer listed one by one in the Help menu; the window lists the editor's tutorials first, then a separate **Plugin tutorials** section.
- **15 tutorials for the editor itself** (`tutorials/`, one topic each): start here, project setup, first mod, canvas, game functions and hooks, variables and math, flow, own functions, pointers, custom code and import, groups / comments / library, output and building, preferences and shortcuts, plugins, troubleshooting.
- **Interface tour** (*Help > Interface tour…*): 11 steps with the part of the window highlighted, Back / Next, Skip, Esc and arrow keys. Shown automatically the first time (after the setup dialog), then never again once completed or skipped; left unfinished it comes back at the next start. Setting `tour_done` in the config.
- New help button actions: `tour`, `settings`. Checked here: headless Qt run of the window, the tutorials window, the whole tour step by step, the released-link menu, the plugin halo.

## v7.5
- **Fix: ZL + ZR blocked the game's buttons even when ImGui had no window** (static text, pictures). The controller now goes to ImGui only while an interactive window is on screen (not a child window, not `NoInputs`, not the fallback "Debug" window); background draw lists don't count.
- **Gamepad settings in the editor.** *Exlaunch base…* of the Dear ImGui plugin has a new **Gamepad** group: *Combo* (two lists: *Hold* + *then press*, any of A B X Y L R ZL ZR + - D-pad, stick clicks; the same button twice = one button), *Automatic* (no combo) or *Never*. The choice is stored with the editor settings and written to `src/odn_imgui_config.h` (generated, tracked by *Remove*); the C++ falls back to hold ZL + press ZR without that file.
- Generic mechanism for plugin authors: `base.settings` in plugin.json (file, template, fields with options and `enabled_if`); values are checked against the options before they reach the C++ file. Documented in PLUGINS.md.
- Dear ImGui plugin 1.3.0; tutorial updated. Checked here: clang syntax check of the ImGui files in the three modes, apply / change settings / revert on a copy of SMO-Exlaunch-Base + OdysseyHeaders, dialog opened headless. Not checked: a real Switch toolchain link and the game.

## v7.4
- **Fix: the game crashed at startup after the ImGui patch** (Ryujinx: invalid access at 0x10 in `strlen`, called from `Logger::log`). The debug output function kept its pointer in a `register asm("x0")` variable while calling `strlen()`, which overwrote it. The registers are now set inside the asm block. Found from the Ryujinx log; confirmed working on a real run.
- **Help pages from plugins.** New `help` key in plugin.json (a Markdown file, optional buttons: `template:<name>`, `base:<plugin id>`, `browser:<plugin id>`, `plugins`); every enabled plugin's pages are listed in the Help menu, and *Help > Help topics…* (F1) opens a non-modal window with a topic list, search and the page, so you can follow it while you work. Without the key, the files of `help/*.md` are used.
- **Dear ImGui plugin 1.2.0:** the tutorial *How to use Dear ImGui*: quick start in five steps, how a draw function works (`Begin` / `End`, Add draw function), finding nodes, values / pointers / printf arguments, recipes (checkbox, slider, FPS counter, overlay, drawing on screen, demo window), controls in the game (ZL + ZR), a troubleshooting table.

## v7.3
- **Dear ImGui now builds on exlaunch + OdysseyHeaders bases** (Fuzzy2319's SMO-Exlaunch-Base). Fixes found by compiling a real project step by step:
  - The payload no longer ships `nn/`, `sead/` or `nvn/` headers (they clashed with the ones of OdysseyHeaders: `nn::Result` redefined, `<time.h>` hidden). Only `glslc`, `nvnTool` and `nvn_CppFuncPtrImpl.h` are added, when missing.
  - New `src/lib.hpp` glue: includes `nn/types.h`, exlaunch's `lib/result.hpp` and `lib/diag/assert.hpp`, and an `R_ABORT_UNLESS` that accepts both `nn::Result` and exlaunch's integer results. `IM_ASSERT` is now a `do { } while (0)` (it broke `if (...) IM_ASSERT(); else`).
  - `Logger` is reduced to debug output (`svcOutputDebugString`): no socket, no `nn::Result`, no `nn/socket.h` (which lacks `in_addr` in OdysseyHeaders).
  - `fsHelper`, `ImguiShaderCompiler`, `imgui_nvn.cpp`: `nn/` include prefixes, `IsSuccess`/`IsFailure`, `lib/hook/trampoline.hpp` for `HOOK_DEFINE_TRAMPOLINE`.
  - `InputHelper`: field names of the open-ead `nn/hid.h` (`mX`, `mKeys`...); game-pad styles missing from older SDKs removed; touch screen reading disabled (the call is not declared there).
  - Frame time from the ARM counter (`cntpct_el0`), so `os/os_tick.hpp` is not needed.
  - Include folders are added only when they exist: `include/NintendoSDK`, `include/NintendoSDK/nvn`, `include/NintendoSDK/nvnTool`, `libs/NintendoSDK`...
- Base patch: the executable target is found even when it is written as a variable (`add_executable(${SUBSDKX})` + `set(SUBSDKX subsdk9)`), and the `target_link_libraries` keyword is read from any call of the project (the v7.2 detection only matched a literal target name, so the CMake error could come back).
- Checked here: the patch applied to a copy of SMO-Exlaunch-Base + OdysseyHeaders, then `clang -fsyntax-only` on every ImGui file (no error in the plugin files; the v7.2 files fail), then Remove restores the project exactly. Not checked here: the real devkitA64 link and the game itself.

## v7.2
- Fix: CMake error "The keyword signature for target_link_libraries has already been used" after the ImGui patch. The block no longer calls `target_embed_binaries` (which uses the plain signature): it embeds imgui.bin with `__add_binary_library` and links it with the same signature your CMakeLists uses (`PRIVATE` or plain). The CMake block now has a revision number: a block written by v7.0 / v7.1 is detected as outdated and replaced by "Exlaunch base..." > Repair (or by the offer shown before Write to project / Compile). Checked with a real CMake run on a mock project (before: error, after: configures).

## v7.1
- Fix: the Dear ImGui base patch said "no CMakeLists.txt" for projects that have one. The project folder is now resolved tolerantly (`odyssey/projectpath.py`): quotes / spaces, `/` and `\\` mixed, `\\wsl$\` and `\\wsl.localhost\`, a Linux path (`/home/me/mod`) with the build in WSL (the distro is found automatically), MSYS / Git Bash paths (`/c/Users/me/mod`), a file (main.cpp) or a sub folder (src/program) instead of the root, a parent folder holding one project, any capitalisation of CMakeLists.txt. When nothing is found, the message lists every folder that was tried.

## v7.0
- **Dear ImGui plugin** (bundled, **disabled by default**): ~350 ImGui functions, 41 ImDrawList methods and ~500 constants as nodes, generated from imgui.h 1.90.6 (`plugins/imgui/tools/gen_catalog.py`), plus *Add draw function*, ImVec2, ImVec4, IM_COL32, flags OR, address of, screen size, frame time, FPS.
- **Function catalogs** in the plugin system: a plugin can ship a big `functions.json`; nodes are built on demand. New **plugin function browser** (Edit > Add plugin function, Ctrl+Shift+K; button in the palette; empty-canvas menu; "Function browser..." in the explorer).
- New node options for plugins: `both` (a statement that can also be used as a value: right-click > Use as a value), `place: "main"` (emitted once inside exl_main, no pins), `init` (lines emitted once in exl_main, de-duplicated), `default_enabled: false`, `catalog`, `templates`, `base`.
- **Exlaunch base patch**: when the plugin is enabled, when its template is loaded or when a graph that uses it is written, the editor offers to add ImGui to the exlaunch project (copy-if-missing, never overwrites; one marked CMake block with a backup; revertible; edited files are kept on removal). Plugin explorer > *Exlaunch base...* shows the state, repairs or removes it.
- **File > New from template**: templates shipped by enabled plugins. *Hello ImGui*: loads ImGui and shows a window with a text and a click counter.
- Unused results of plugin statements are no longer stored in an unused variable.
- Credits and licences: CraftyBoss SMO-Exlaunch-Base (GPL-2.0), LunaKit (GPL-2.0), exlaunch, exlaunch-cmake, Dear ImGui (MIT); see `plugins/imgui/NOTICE.md` and `plugins/imgui/LICENSES/`.

## v6.0
- **Plugin system** (Plugins menu, Ctrl+Shift+P). A plugin is a folder (or a .zip / .odnp) with a plugin.json: it can add **nodes** (declarative C++ templates with typed pins, fields, includes and helper code), **themes**, and, with an optional plugin.py, menu commands. Documented in PLUGINS.md.
- **Plugin explorer**: lists every plugin with its square picture, title, author, version and description (defaults when missing), shows what it contains and its problems, and lets you enable / disable, install (archive or folder), remove, create a new plugin skeleton, reload and open the folder.
- Graphs keep a copy of the plugin nodes they use (also saved functions in the library), so they still work when the plugin is disabled or missing.
- **Bundled plugins**: *Standard I/O* (printf, puts, snprintf, sscanf, fopen / fgets...), *Strings* (strlen, compare, contains, copy, atoi...), *Extra themes* (Midnight, Solarized Light, Mario Red).
- **Keyboard shortcuts**: Tools > Keyboard shortcuts... lists every command (and plugin commands); click a shortcut, press the new keys; conflicts are flagged; reset one / all.
- Theme menu and Preferences list the themes added by plugins; new "Theme default" accent.

## v5.4
- The graph icon bar is rebuilt from plain fixed-size buttons (left / centre / right groups): no more squeezed icons, no overflow chevron, centre group really centred. "Made by WibiDev" moved to the bottom-left of the status bar.

## v5.3
- Fix: the toolbar spacers and the status bar widgets were drawn as grey boxes (theme background); icons are bigger and better spaced. Any leftover window toolbar from an older saved layout is hidden. "Made by WibiDev" sits in the bottom-right corner of the status bar.

## v5.2
- The icon bar now sits at the top of the graph area (not above the whole window). Clear shows its label next to the icon; the catalog uses the book icon again.
- "Made by WibiDev" highlighted at the top of Help > About and shown in the status bar.

## v5.1
- **Toolbar layout**: left = New, Open, Save as | Undo, Redo; centre = Clear, Fit view, Find in graph; right = Open the catalog, Preferences. Group, Comment and Library were removed from the toolbar (still in the menus and right-click).

## v5.0
- **Real icons instead of emojis / symbols**: a small vector icon set (drawn from SVG paths, no image files) is used in the toolbar, the output panel buttons, the block palette, the Problems list, the search bar, the function browser (star, GitHub link), list editors and the Ryujinx panel. Icons follow the theme.
- **Toolbar**: icon only (tooltip = name + shortcut). Write to project / Compile are no longer there (they stay in the panel below); search was added.
- **Themes**: View > Theme (Dark / Light) and View > Theme > Accent color (Red, Orange, Amber, Green, Teal, Blue, Purple, Pink); also in Preferences > General > Appearance. Applied live, remembered. The canvas, nodes, code colors, search bar and combo arrows follow the theme.
- **Startup graph**: File > Save as startup graph and Forget the startup graph now ask for confirmation.
- **Credits**: WibiDev added (Help > About).
- **Version**: the version shown in the window title and in About is now read from one place (`odyssey/__init__.py`); it had stayed on 4.2.1 since 4.3. (4.2.1 is the only three-number release.)

## v4.6
- **Catalog: every entry of file_list.yml** when the Filter is empty (Settings; the default filter is unchanged). The reader is now a real list parser: labels given as a list of aliases (constructors C1/C2, 3929 entries), quoted labels, thunks, operators, templates, plain C names and entries without a label (named `sub_<offset>`, hooked / called by offset) are all kept. On the current OdysseyDecomp: 74171 entries, all present (it used to miss about 4000). Names that are not plain C++ identifiers are called by address automatically. Extract the catalog again to get it.

## v4.5
- **Constructors in the function browser**: extract the catalog again (Settings) and constructors such as `ChangeStageInfo(...)` are listed; choosing one adds a **Construct** block with the real argument types (option: `new`). Destructors stay hidden. Without re-extracting, use the *Construct (new / Type(...))* block from the palette and type the class name and the argument types.

## v4.4
- Fix: the right-click menu had two "Use as a value" entries and the option was greyed out for functions the catalog marks as void. One entry now; on a void function it sets the return type to "auto" so the result can be used.

## v4.3
- **Use as a value (no execution pins)** is now an option of the right-click menu of a call node (checkable; disabled when the call returns void). It is no longer a check box in the inspector.

## v4.2.1
- Right-click a call node > **Use as a value (hide execution pins)** (checkable): hides / shows its execution pins, e.g. to feed its result into a variable or another block.

## v4.2
- **C++ import**: `x += y`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=`, `>>=` on variables, members (`pos.x -= 1`) and array elements (`counts[2] += 1`); `a[i]` and `a[i] = v`; arrays (`int t[4] = {...}`, global or local), `static` / `constexpr` qualifiers (no longer dropped on globals); template calls such as `al::getSceneObj<GameDataHolder>(scene)`.
- **New blocks**: *Array element a[i]*, *Set array element*, and *Get scene object al::getSceneObj<T>* (template call: set the type in "Template arguments"; "Call by name" has the same field and `$T` in its return type stands for it). The math block also does `& | ^ << >>`.
- **Variables**: qualifier (static, const, constexpr...), array size and array contents, in a collapsed **Advanced** section of the inspector (opens by itself when used).
- **Groups**: linking two nodes also groups them (the one without a group joins the other's group) when auto-grouping is on.
- **Link released on empty space**: opens the add-a-block menu (only blocks that fit the pin; "Game function…" first); the new block is created there and connected. Option in Preferences > Canvas.
- **Function browser**: hovering or clicking the ↗ and ★ cells no longer changes the selected function (they are plain cells now, not buttons), and a double-click on them does not add the function.

## v4.1
- **C++ import, far fewer custom nodes**: calls without their namespace (`isHidePane(...)`, `getTrans(...)`) are found in the catalog by the end of their name (al:: / rs:: preferred; an ambiguous name stays a call by name). New blocks **Call by name** (any function not in the catalog, e.g. `sead::Mathf::sqrt(x)`) and **Construct** (`Type(args)`, `new Type(args)`, `Type v = {a, b, c}`). Declarations such as `auto* x = new T(...)`, `T v(...)`, `T v = {...}` become real variables (they used to be custom statements, which turned every later use of the variable into a custom expression). Globals declared as `T name(args);` are imported. Your main.cpp: 66 custom nodes before, 0 now.
- Import: a hook whose symbol is not in the catalog no longer crashes the import (the symbol is kept).
- **Save result as**: the variable is shown in a highlighted pill inside the block ("→ saved in player") and the result pin carries the variable name.
- **Find in the graph** (Ctrl+F, also right-click on the canvas or on a node): grey out every node that does not mention what you typed (variable, function, expression, value, name...). Enter / Shift+Enter jump to the next / previous match. *Add game function* moved to Ctrl+Shift+F.
- The buttons of the confirmation boxes (import: replace / add...) are wide enough for their text.

## v4.0
- **Simple calls**: a game function is now called like in your own code: `rs::getPlayerActor(scene)`, `al::setTrans(actor, 1.0f, 2.0f, 3.0f)`, `GameDataFunction::isGotShine(...)`, `obj->method(...)` for a member (instead of `reinterpret_cast<...>(GetTargetOffset(0x...))`). Choose the style in Preferences > Advanced, or per block (Call style in the inspector). The by-address form is still there as an option.
- **Catalog fix**: static functions of a class (e.g. `GameDataFunction::...`) no longer get a fake "this" argument. Extracting the catalog again records which functions are static; with an older catalog the class name is used to guess (…Function, …Util). Saved graphs that call such functions have one argument less: reconnect if needed.
- **C++ import**: direct calls (`rs::fn(...)`, `Class::fn(...)`, `obj->method(...)`), `HOOK_DEFINE_REPLACE` hooks, and `Orig(...)` anywhere in a hook (new **Call original (Orig)** block + hook mode **Manual**; first / last stays "before" / "after"). `x++` was already handled. A call whose result is used keeps its type even when the catalog says void.
- Hooks in Replace mode are generated with `HOOK_DEFINE_REPLACE`.
- File > New puts the standard includes back (it used to keep the previous ones).
- **Zoom**: new limits 3% - 600%; Fit and the wheel can always bring a far-away graph back.
- **Operator nodes**: smaller (true squares), with the node name in the colored top bar; conditions are shown as words / math signs (AND, OR, NOT, =, ≠, ≤, ≥); `+ - * / %` stay as they are.
- **Groups**: right-click a node placed over a group > "Put into the group ...". Option (Preferences > Canvas): a node dropped inside a group frame joins it (only nodes without a group).
- **Line numbers** in the code preview (Preferences > Code preview).
- **Bool constants** are a check box in the inspector.
- **Ryujinx**: before starting the game, all other mods are turned off in Ryujinx's `games/0100000000010000/mods.json` (option, on by default). The original file is saved once; "Re-enable other mods" restores it.

## v3.0
- **Math & logic nodes are small squares** (symbol in the middle, type below, fixed values next to their pin) to save space.
- **File > New option** (Preferences): show your startup graph (empty if none was saved) or nothing. The example graph is no longer shown by New.
- **Clear the graph** button / Edit menu (with confirmation, undoable).
- **Groups**: double-click a group (or right-click > Edit group) to change its name, color and nodes; right-click a node > "Add to group" or right-click a group > "Add the selected nodes to this group". Colors have names (Blue, Green, Orange, Purple, Red, Teal, Pink, Yellow, Gray) with a swatch instead of hex codes. Group creation uses the same window.
- **Import C++**: `x++`, `x--`, `++x`, `--x` are converted (`x = x + 1`), as `x += n` already was.
- **Favorites**: ☆ at the end of each row of the function browser; "★ Favorites only" filter; favorites are listed first. Saved in your settings.
- **Option: links of the selected node on top** of everything else (Preferences > Canvas).
- **Compile** shows its two steps in the Build tab: 1) the code is written into the project (path and line count), 2) the build command, then the duration and the main errors. It warns when the graph has errors, and offers `make` when the project has a Makefile and the command is still the default `cmake --build build`.
- **Ryujinx "Install mod"** now empties the mod folder (`.../0100000000010000/<name>`) before putting the new `exefs` in it (it refuses any folder that is not exactly that mod folder).

## v2.7
- Ryujinx launch: the program is now started with its input closed and its output written to `ryujinx_launch.log` (in the data folder), without a console window. A GUI program started from the window-less .exe used to inherit invalid console handles and could die silently.
- The "ok" in the console only meant "process created". Three seconds later the tab now checks that Ryujinx is still running ("✔ running (pid ...)"), or shows the exit code and the last lines of its output.

## v2.6
- Ryujinx tab: only `subsdkN` and `main.npdm` are copied (no more `.elf`, `.json`, `.specs`...). The number is read from `set(SUBSDKX subsdk9)` in `CMakeLists.txt` (next to the build folder); if it is not there, the build folder is searched for subsdk9, 8, 7... down to 0. The "Files to copy" field is now optional (empty = automatic).

## v2.6
- Ryujinx: only the exact files are copied (default `subsdk9;main.npdm`), never `subsdk9.elf`, `.json`, `.Id`, `.specs`. With the default (or an empty field) the number after `subsdk` is read from `set(SUBSDKX subsdk9)` in `CMakeLists.txt` (next to the build folder); if absent, the first of subsdk9 ... subsdk0 found in `build` is used.
- Slashes: paths are made consistent with the OS. `//wsl.localhost/Ubuntu/...` used to be mistaken for a Linux path (and doubled); now a single leading `/` means "inside WSL", a double one means "network / WSL share". Paths chosen with the Browse buttons (which give `/`) are converted to `\\` on Windows.

## v2.5
- New **Ryujinx** tab in the bottom panel: one click copies the compiled files (`subsdk*`, `main.npdm`, configurable) from the build folder into `<Ryujinx data>/mods/contents/0100000000010000/<your mod name>/exefs`, then starts the game.
- Settings: Ryujinx executable, data folder (detected automatically: portable folder, `%APPDATA%\\Ryujinx`, `~/.config/Ryujinx`; asked if not found), game file (Ryujinx cannot start by title ID), mod folder name, build folder (default `<project>/build`, reached through `\\\\wsl.localhost\\<distro>` when the project is in WSL), files to copy, extra options, fullscreen, optional "compile first".
- Buttons: Install and launch / Install only / Launch only / Open mod folder.

## v2.4
- Fix: the namespace is now added to the return type of a call even when it comes from a return-type override you set (`LiveActor*` -> `al::LiveActor*` in the cast), and for method calls.

## v2.3
- Fix compile errors seen in a real build: class names the catalog gives without a namespace (`LiveActor*`) are now qualified (`al::LiveActor*`) in return-type casts and in variable declarations.
- Fix `exl_exception_entry`: generated `EXL_ABORT("Unhandled exception")` (this exlaunch version wants a format string, not a number).
- Hooks are installed with `InstallAtSymbol("<mangled name>")` by default; a hook with an unknown symbol falls back to `InstallAtOffset`. The choice is in Preferences > Advanced. The C++ import understands both forms.
- Build tab: **Save log as...** button.
- Preferences window now has General / Advanced tabs.

## v2.2
- Fix WSL builds: a project folder written as `//wsl.localhost/Ubuntu/home/...` (forward slashes) was passed to WSL as-is and failed with "chdir ... failed 2". It is now converted to the Linux path (`/home/...`) and the distro is taken from it.
- Build tab: **Copy log** (whole console) and **Copy errors** (only error / warning / failure lines) buttons.

## v2.1
- New **Repair base** button (and Tools > Repair exlaunch base): after a confirmation it deletes the project's `build` folder, then runs `cmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake` (WSL / Windows / native, same as Compile).
- Generated code now starts with `#include <exlaunch.hpp>` (was `"lib.hpp"`); the C++ import ignores that line.

## v2.0
Big update.
- **Import C++**: File > Import C++ file reads a `.cpp` and rebuilds a graph (hooks, functions, globals, if/else, loops, switch, calls of game functions, math, pointers, casts). Whatever it cannot understand stays as a custom statement / expression, so the code is equivalent. Comments are not kept.
- **Library**: save a function (with everything it uses) or any selection as a `.odnf` file in your data folder, list it in the block panel and Library menu, insert it again (inside a group, names are de-duplicated). Rename / delete in Library > Open the library.
- **Groups and comments**: frames around nodes (Ctrl+G, drag the title to move them all) and free comments on the canvas. Imported functions are grouped automatically. Edit > Arrange nodes automatically (Ctrl+L).
- **Boxes + button**: function arguments, switch cases and method argument types are edited as one small box per item with a "+ Add" button and a remove button.
- **Call as a value**: a call can be used inside other blocks (no execution pin) with "Use as a value". New **Call method (->)** block for methods of pointers/objects.
- **Return type of game functions** can be changed (with a warning and a confirmation), for one block or for every call of that function (remembered).
- Custom functions and their calls show the type they return on the block.
- A "Declare variable" block outside any function becomes a global variable; the Global variable block has a value output.
- Game function browser: a button next to each function (and in the details) opens the name in a GitHub code search of MonsterDruide1/OdysseyDecomp.
- The generated line(s) of the selected node are highlighted in the code preview.
- Startup graph: File > Save as startup graph is what File > New (and optionally the program start) opens.
- Preferences menu (Ctrl+,): startup behaviour, autosave, grid and snapping, code font and wrapping, line highlight, text size.
- main.cpp is looked for in `src/program/main.cpp` and `src/main.cpp`.
- Graphs are saved as `.odn` only; `.json` files can still be opened.
- Drop-down arrows are now a square button as tall as the box.
- Settings: the "Filter (regex)" field has a tooltip and a hint explaining what it does.
- Custom code blocks accept up to 8 inputs ($a ... $h); a For loop can name its index variable; a hook can name its arguments.

## v1.2
- Build environment setting: Windows (cmd), WSL (choose the distro, e.g. Ubuntu) or native shell. The first Compile on Windows asks which one to use. WSL builds run `wsl.exe -d <distro> --cd <project> -e bash -lc "<command>"`; `\\wsl$\...` project paths are converted automatically.

## v1.1
- Version number shown in the window title and the About box; changelog added.

## v1.0
- First release: node editor, game function browser / block builder, typed fixed inputs, inspector, collapsible output panel, Compile button, logo, one-step `build_exe.bat`.

Note: the program is now displayed as "Odyssey Node Editor" (name only; data folder and OdysseyNodes.exe keep their names).
