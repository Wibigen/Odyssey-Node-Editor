# Start here

The **Odyssey Node Editor** lets you build a **Super Mario Odyssey 1.0.0** mod without writing C++ by hand. You connect **nodes** on a canvas, and the editor writes the [exlaunch](https://github.com/shadowninja108/exlaunch) code for you. You still compile it with your own exlaunch project.

## The idea in one minute

1. A **hook** node says *"when the game runs this function, run my graph"*.
2. You connect nodes after it: call game functions, change variables, test conditions, loop.
3. The **C++ code** tab shows the result live.
4. **Write to project** puts the code in your exlaunch project, **Compile** builds it, the **Ryujinx** tab launches the game with your mod.

## What you need

* A folder with **OdysseyDecomp** (the editor reads its symbol list to know every game function).
* An **exlaunch project** (for example a copy of SMO-Exlaunch-Base) that you can build.
* *(optional)* Ryujinx, to test.

## The window

| Part | What it is |
|---|---|
| Menus + tool bar | File, Edit, Library, View, Tools, Plugins, Help; the icons you use most |
| **Blocks** (left) | Every block you can add, searchable |
| **Canvas** (centre) | Your graph |
| **Inspector** (right) | Settings of the selected node |
| **Output** (bottom) | C++ code, Includes, Problems, Build, Ryujinx |

Press **Help > Interface tour** for a guided presentation, then follow the tutorials in order:

1. *Set up your project*
2. *Your first mod*
3. *The canvas*, then the topics you need.

**Good to know:** the editor never compiles for the Switch by itself and never touches your game files: it writes C++ into the project you point it at.
