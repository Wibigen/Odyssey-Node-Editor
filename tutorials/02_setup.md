# Set up your project

Open **Tools > Settings** (Ctrl+Shift+,). It opens by itself the first time.

## 1. The OdysseyDecomp folder

Choose the folder of your [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) copy (the one that contains `data/file_list.yml`). The editor then builds the **function catalog** (about 17,700 functions): names, arguments, return types, offsets and symbols. This is done once and saved. It needs the `c++filt` tool to read mangled names; it is found automatically, or set it in the same window.

If the catalog says `void` for a function that really returns something, you can fix it later (see *Calling and hooking game functions*).

## 2. Your exlaunch project

* **Project folder**: the root of your exlaunch project (the one with `CMakeLists.txt`). Windows paths, `\\wsl$\Ubuntu\home\me\proj` and WSL paths are understood.
* **Generated file**: where the code is written. Empty = `src/program/main.cpp` or `src/main.cpp`, whichever exists.

## 3. The build command

Default: `cmake --build build`. Choose where it runs: **Windows (cmd)**, **WSL** (pick the distro, for example Ubuntu) or the native shell. The first *Compile* asks if it is not set.

## 4. Test it

Open the **Ryujinx** tab (bottom), set the Ryujinx executable, the game file and a mod name once. *Install mod and launch* copies your build into Ryujinx's mod folder and starts the game.

## If something is not found

* **Problems** tab: what the graph still needs.
* **Tools > Repair exlaunch base**: deletes the `build` folder and runs CMake again (fixes a broken setup).
* Settings can be reopened any time; nothing is lost.
