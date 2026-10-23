# Dear ImGui in your Super Mario Odyssey mod

Dear ImGui draws small windows (text, buttons, sliders, checkboxes, graphs...) **on top of the game**, every frame. With this plugin you build those windows with nodes, and the editor writes the C++ for your exlaunch mod.

**You will need:** an exlaunch project (the tested layout is *SMO-Exlaunch-Base* with *OdysseyHeaders* in `include/`), Super Mario Odyssey 1.0.0, and Ryujinx or a modded Switch.

## 1. Quick start (5 minutes)

1. **Enable the plugin.** *Plugins > Plugin explorer*, switch *Dear ImGui* on. It is off by default because it adds files to your project.
2. **Let the editor prepare your project.** It offers *Add to my project*. It copies the ImGui sources and its Switch backend (only files your project does not already have), and appends **one marked block** to `CMakeLists.txt` (a backup `CMakeLists.txt.odn-backup` is kept). *Plugin explorer > Dear ImGui > Base…* shows the state, repairs it, or removes exactly what was added.
3. **Load the example.** *File > New from template > Hello ImGui*. (Use the button at the top of this window.)
4. **Write and build.** *Write to project* (Ctrl+E), then *Compile* (F5) or your usual `make`.
5. **Run the game.** A window appears with a text and a button that counts presses.

> Tip: the first time, check that the build log has no error before looking for problems in the game.

## 2. How it works

Every frame, the backend calls the functions you registered. Each of them draws ImGui widgets, **always between `Begin` and `End`**:

```
Begin("My window")
  Text("Hello")
  Button("Click me")  ->  if it returns true, the button was pressed
End()
```

In the graph:

* A **Define function** node (no argument, returns `void`) holds the drawing, for example `drawHello`.
* An **Add draw function** node (category *Dear ImGui*) registers it. It has no execution pins: it is written once at the start of the mod, and it also installs the ImGui hooks. You need exactly one per draw function.
* Inside the function, chain ImGui nodes with the **execution pins**, like any other node.

Rules to remember:

* Call `End` even when `Begin` returned false (collapsed window).
* ImGui calls only work **inside a draw function**. Do not call them from your own hooks.
* A widget that returns a `bool` (Button, Checkbox, SliderFloat...) says "the user changed or pressed it". Plug it into an **if** node.

## 3. Finding the nodes

There are about 900 entries: ~350 functions, the `ImDrawList` methods and ~500 constants (flags, colours, keys).

* **Edit > Add plugin function…** (Ctrl+Shift+K) opens the browser: type a word (`slider`, `colour`, `window flags`), see the signature and the description, double-click to add. *Keep open to add several*.
* Also in the right-click menu of the canvas and in the palette.
* Entries come in three kinds: **functions** (`Button`), **methods** of a draw list (`AddRectFilled`), and **constants** (`ImGuiWindowFlags_NoMove`).

Helper nodes (category *Dear ImGui: values*): **ImVec2**, **ImVec4**, **Colour 0-255 (IM_COL32)**, **Combine flags (a | b)**, **Address of (&variable)**, **Screen size**, **Frame time**, **Frame rate (FPS)**.

## 4. Values, pointers and text

* **Text with numbers.** `Text`, `TextColored`, `Button`... take a printf format. For `Text("Button pressed %d times", clicks)` write the format in the *fmt* field, then set **Number of arguments** on the node (the pins appear) and plug your values in.
* **Widgets that edit a variable** (Checkbox, SliderFloat, InputInt, ColorEdit4…) want a **pointer**. Use the **Address of** node and type the name of a *global variable* (create it with a *Global variable* node, category *Variables*), or type `&myVar` in the field.
* **Use a result directly.** Right-click a node > **Use as a value** hides its execution pins, so its result can feed another node (for example `ImVec2(...)` into `SetNextWindowSize`).
* **Save a result.** Many statement nodes have *Save the result in a variable named*.
* **Flags.** Combine them with **Combine flags**: `ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoMove`.

## 5. Recipes

**A checkbox that switches something on.**
Global `bool godMode = false`. In the draw function: `Begin` > `Checkbox("God mode", &godMode)` > `End`. In any other part of your mod, read `godMode`.

**A slider.**
Global `float speed = 1.0f`. `SliderFloat("Speed", &speed, 0.0, 5.0)`. Use `speed` elsewhere.

**FPS counter.**
`Text("%.1f FPS", Frame rate)` with one variable argument.

**Fixed, transparent overlay.**
Before `Begin`: `SetNextWindowPos(ImVec2(10,10), ImGuiCond_Always)` and `SetNextWindowBgAlpha(0.35)`. Use the flags `NoTitleBar | NoMove | NoResize | AlwaysAutoResize`.

**Draw directly on the screen.**
`GetBackgroundDrawList()` returns an `ImDrawList*`. Plug it into the **object** input of a method node such as `AddRectFilled`, `AddLine`, `AddCircleFilled` or `AddText`. Colours come from **IM_COL32(r, g, b, a)**.

**Look at everything ImGui can do.**
`ShowDemoWindow(NULL)` in your draw function opens the official demo. It is a good place to see which widget you want, then search its name in the browser.

## 6. In the game

* **Mouse and keyboard** (for example in Ryujinx) always work.
* **Controller:** by default, hold **ZL** and press **ZR** to give the controller to ImGui (the game stops reacting to it); do it again to give it back. This only has an effect while an *interactive* ImGui window is on screen: text or pictures drawn on the background (`GetBackgroundDrawList`) or windows created with `NoInputs` never take the controller from the game.
* **Change the combo:** *Plugins > Plugin explorer > Dear ImGui > Exlaunch base…*, group **Gamepad**. Pick the two buttons (*Hold* and *then press*; the same button twice means a single button), or choose **Automatic** (ImGui has the controller as long as one of its windows is shown, no combo) or **Never** (mouse and keyboard only). The choice is written into `src/odn_imgui_config.h` of your project: rebuild with `make`.
* The touch screen is read only when the SDK headers of your project declare it. With the headers of *OdysseyHeaders* it is disabled.
* ImGui places a new window near the top left; drag it where you want.

## 7. When something goes wrong

| Symptom | What to do |
|---|---|
| CMake error about `target_link_libraries` | *Plugin explorer > Dear ImGui > Base… > Repair* rewrites the block (it uses the same signature as your project). |
| "No such file" for an ImGui or nvn header | *Base…* shows what is missing; *Repair* adds it. Rebuild. |
| The game crashes at startup | Read the Ryujinx log: the **guest stack trace** shows the function. The backend prints lines starting with `Creating ImGui…` to the debug output (`OutputDebugString` in the Ryujinx log). |
| The game runs but nothing is drawn | Is there an **Add draw function** node pointing at your function? Is `Begin`… `End` inside it? Did you rebuild after *Write to project*? |
| The window is empty or looks wrong | Look at the debug output for the lines the backend writes about the shader, and make sure the CMake block embeds `romfs/ShaderData/imgui.bin` (*Base…* shows it). Send the log if you ask for help. |
| You want to undo everything | *Plugin explorer > Dear ImGui > Base… > Remove from my project*. Files you edited yourself are kept. |

## 8. Good to know

* The generated code goes in `main.cpp` like the rest of your graph. ImGui nodes need the ImGui headers, which the plugin adds to the includes automatically.
* One draw function per feature keeps the graph readable; you can register as many as you like.
* ImGui uses a bit of the game's memory. Avoid thousands of widgets per frame.
* This is an unofficial mod tool. Test on an emulator or a console you own, with your own copy of the game.

## Credits

Backend: *SMO-Exlaunch-Base* by **CraftyBoss** (GPL-2.0), based on *LunaKit* by **Amethyst-szs** (GPL-2.0). Dear ImGui by **Omar Cornut** (MIT). exlaunch by **shadowninja108**. Headers: **open-ead** and **MonsterDruide1** (OdysseyHeaders).
