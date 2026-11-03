# Task: add Spider-Man Remastered, Sonic Frontiers and Sonic Colors: Ultimate to ModSwap

You are running ON the owner's Windows PC, so you can read their real game files. The cloud session that wrote this could not.
Do not stop after a plan: keep going until the work is built, tested and pushed. Time is not a constraint.

## What ModSwap is
A tool that swaps a character's model in a game for a custom model (with textures) and can undo it.
* `modswap/` - Python engine. Today it only handles **Unreal** (`modswap/ue4/`, `modswap/project.py`) and **Unity** (`modswap/unity/`).
* `ModSwap.exe` - Windows app (WPF). Its source is in `ui-recovered/` (read `ui-recovered/RECOVERY.md`). It talks to the engine over a local HTTP API in `modswap/server.py`.
* Read `README.md` (sections 2.13 and 2.14) first. Tests are in `tests/` (`python tests/<file>.py`).

## How an engine plugs in (follow the existing pattern)
* `modswap/games/detect.py`: `detect_engine()` recognises a game, `SUPPORTED` lists engines that can be swapped.
* `modswap/server.py`: `_project(g)` returns the project object for a game; it must offer the same methods the UI already calls
  (see `modswap/unity/project.py` for the shape: describe/scan characters, geometry/fit, build, install, uninstall, restore, mods stack).
* `modswap/unity/` is the closest model to copy: it replaces mesh/texture data inside the game's own files with backups, undo, and stacking.
* The UI marks a game swappable from the `supported` field of `/api/games`, so a new engine only needs `SUPPORTED` + a project class. Change the C# only if you must,
  and if you do, rebuild with `dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o publish` in `ui-recovered/`.

## The three games (Steam, usually `C:\Program Files (x86)\Steam\steamapps\common`)
1. **Marvel's Spider-Man Remastered** (Insomniac engine). Characters and **textures must both work**.
   The owner already had a build where Spider-Man swapped in-game with no textures. FIRST search the PC for it
   (`Get-ChildItem C:\Users\xavie -Recurse -Include *.py,*.cs,*.zip | Select-String spider`) and reuse that format code.
2. **Sonic Frontiers** (Hedgehog Engine 2, `.pac` archives).
3. **Sonic Colors: Ultimate**.

## Rules
* NEVER guess a file format. List the install, read real files, write the parser, then **verify by re-reading your own output** (the repo's other engines do this).
  Say plainly what you verified and what you could not (for example "not launched in the game").
* Back up every original game file before changing it; uninstall and "Put the game back to normal" must restore byte for byte.
* Refuse to touch a game that is running (see `modswap/games/running.py`).
* Add tests under `tests/` for each parser/writer (use small synthetic files if a real one is too large to commit). Never commit game files.
* Do not break Unreal/Unity support: run all tests in `tests/` before every commit.
* Commit in small steps to branch `claude/keen-brown-fcf6ri` and push. Update `README.md` with a new version section and an honest "not verified" list.

## Done means
For each of the three games: ModSwap lists its characters, a custom model with its textures can be swapped in and shows correctly (textures included),
uninstall restores the original, and all tests pass. If one game is truly impossible (encrypted/unknown format), write down exactly why with evidence from the files.
