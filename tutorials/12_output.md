# Code, problems and building

The **Output** panel at the bottom has five tabs. Collapse it with the arrow, **Ctrl+J**, or a double-click on a tab.

## C++ code

Live preview of the generated file. The lines of the **selected node** are highlighted. **Copy** and **Save as…** export it.

## Includes

The headers at the top of the file (see *Custom code*).

## Problems

What is missing or wrong **before** you compile: unconnected inputs, unknown variables, empty hooks. Double-click a line to jump to the node.

## Build

* **Write to project** (Ctrl+E) saves the code into your exlaunch project.
* **Compile** (F5) runs the build command and shows the output. **Copy errors** copies only the error lines; **Save log as…** keeps the whole console.
* **Repair base** (Tools menu) deletes `build/` and runs CMake again.

## Ryujinx

Set the emulator, the game file and a mod name once. **Install mod and launch** copies `subsdkN` and `main.npdm` from your build folder into Ryujinx's mod folder and starts the game. Options include compiling first, disabling other mods and fullscreen.

## Important

The editor itself never builds for the Switch: your project's toolchain does. If a build fails, copy the log (it tells exactly which file and line).
