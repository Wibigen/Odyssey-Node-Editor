# Dear ImGui plugin: credits and licences

This plugin bundles source code from other projects. Their licences apply to the files in `base/`.

| Part | Origin | Licence |
|---|---|---|
| `base/src/imgui_backend/`, `base/src/program/imgui_nvn.*`, `base/src/helpers/`, `base/src/logger/`, `base/romfs/ShaderData/imgui.bin` | [SMO-Exlaunch-Base](https://github.com/CraftyBoss/SMO-Exlaunch-Base) by **CraftyBoss** | GPL-2.0 (`LICENSES/GPL-2.0-SMO-Exlaunch-Base.txt`) |
| ImGui backend for nvn, input and draw hooks | derived from [LunaKit](https://github.com/Amethyst-szs/smo-lunakit) by **Amethyst-szs** | GPL-2.0 |
| exlaunch hooks (used by the generated code) | [exlaunch](https://github.com/shadowninja108/exlaunch) by **shadowninja108**, CMake port by **EngineLessCC** | see their repositories |
| `base/imgui/` | [Dear ImGui](https://github.com/ocornut/imgui) 1.90.6 by **Omar Cornut** and contributors | MIT (`LICENSES/MIT-ImGui.txt`) |
| `base/libs/NintendoSDK` (glslc, nvnTool), `base/src/program/nvn_CppFuncPtrImpl.h` (headers only) | [nnheaders](https://github.com/open-ead/nnheaders) by **open-ead** and the [OdysseyHeaders](https://github.com/MonsterDruide1/OdysseyHeaders) fork by **MonsterDruide1** | see their repositories |

The files of `base/src/` were adapted (v1.1.0 of the plugin) to bases that use OdysseyHeaders; see CHANGELOG.md of the editor, v7.3. The adaptations stay under the licence of the original files.
| `functions.json` | generated from `imgui.h` by `tools/gen_catalog.py` | MIT (Dear ImGui) |

The Odyssey Node Editor plugin files (`plugin.json`, `nodes.json`, `templates/`, `tools/`, icon) are by WibiDev.
The files copied into your project keep their original licence: if you distribute a mod that contains them, respect the GPL-2.0 terms.
