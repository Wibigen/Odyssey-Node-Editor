# Changelog
Versioning: +1 for a big update, +0.1 for a small one.

## v1.2
- Build environment setting: Windows (cmd), WSL (choose the distro, e.g. Ubuntu) or native shell. The first Compile on Windows asks which one to use. WSL builds run `wsl.exe -d <distro> --cd <project> -e bash -lc "<command>"`; `\\wsl$\...` project paths are converted automatically.

## v1.1
- Version number shown in the window title and the About box; changelog added.

## v1.0
- First release: node editor, game function browser / block builder, typed fixed inputs, inspector, collapsible output panel, Compile button, logo, one-step `build_exe.bat`.
