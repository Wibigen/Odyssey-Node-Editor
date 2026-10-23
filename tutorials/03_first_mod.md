# Your first mod

Goal: run something **once per second** during gameplay. The example graph does this; here you build it yourself so you know every part.

## 1. Hook a game function

1. Click **Game function…** (red button, or Ctrl+Shift+F).
2. Search `exePlay`, select **StageScene::exePlay** (it runs every frame while you play).
3. Choose **Hook this function**, keep the mode *Run the original first, then my graph*, press **Add to graph**.

A red **Hook StageScene::exePlay** node appears. Its white **next** pin is where your logic starts.

## 2. Count frames

1. Add a **Global variable** (Variables): type `int`, name `frames`, initial value `0`. A global keeps its value from one frame to the next.
2. Add **Set variable**, choose `frames`, connect **hook next → in**.
3. Add **Get variable** `frames` and **Math (A + B)** with type `int`, B = `1`; connect *Get → A*, *Math out → Set v*.

## 3. Do something every 60 frames

1. Add **Branch (if / else)** after the Set variable.
2. Condition: **Compare** `(frames % 60) == 0` (a *Math* node with `%` and 60 feeding a *Compare* with `== 0`). Connect the result to the Branch's **c** pin.
3. Put what you want on the **then** path, for example a **Custom statement** `/* my code here */`, or a game function call.

## 4. Look at the code

Open the **C++ code** tab: the hook, the variable and the `if` are there. Select a node: its lines are highlighted.

## 5. Build and try

1. **Problems** tab empty? Good.
2. **Write to project** (Ctrl+E), then **Compile** (F5).
3. **Ryujinx** tab > *Install mod and launch*.

> Faster start: **File > New from template** (or the example graph in Preferences > Open on) gives a ready graph.
