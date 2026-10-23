# 设置项目

打开 **工具 > 设置**(Ctrl+Shift+,)。首次运行时该窗口会自动打开。

## 1. OdysseyDecomp 文件夹

选择你的 [OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) 副本文件夹(包含 `data/file_list.yml` 的那个)。编辑器会构建 **函数目录**(约 17,700 个函数):名称、参数、返回类型、偏移和符号。此操作只做一次并会保存。读取经过修饰(mangled)的名称需要 `c++filt` 工具;它会被自动找到,也可以在同一窗口中指定。

如果目录中某个函数显示为 `void`,而它实际上有返回值,可以稍后修正(参见 *调用和钩住游戏函数*)。

## 2. 你的 exlaunch 项目

* **项目文件夹**:exlaunch 项目的根目录(包含 `CMakeLists.txt` 的那个)。支持 Windows 路径、`\\wsl$\Ubuntu\home\me\proj` 和 WSL 路径。
* **生成的文件**:代码写入的位置。留空 = `src/program/main.cpp` 或 `src/main.cpp`,以存在的为准。

## 3. 构建命令

默认:`cmake --build build`。选择运行环境:**Windows (cmd)**、**WSL**(选择发行版,如 Ubuntu)或自定义 shell。如果未设置,第一次 *编译* 时会询问。

## 4. 测试

打开底部的 **Ryujinx** 标签页,一次性设置 Ryujinx 程序、游戏文件和 Mod 名称。*安装 Mod 并启动* 会把你的构建结果复制到 Ryujinx 的 Mod 文件夹并启动游戏。

## 如果找不到某些内容

* **问题** 标签页:图还缺少什么。
* **工具 > 修复 exlaunch 基础**:删除 `build` 文件夹并重新运行 CMake(修复损坏的配置)。
* 设置可以随时重新打开;不会丢失任何内容。
