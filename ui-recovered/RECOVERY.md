# Source of ModSwap.exe 2.14.0 (recovered, now builds)

The Windows app's C# source wasn't in the repo, so it was recovered from the 2.13.0 `ModSwap.exe` (ILSpy 8.2: unpack the single-file bundle, decompile `ModSwap.dll`)
and made to compile again. `ModSwap.exe` in the repo root is built from this folder.

* `ModSwap/*.cs` - all the UI logic (MainWindow, Api, Backend, Viewer3D ...). Method/class names are intact; local variables are `val1, val2 ...`.
* `ModSwap.g.resources` - the window layouts (compiled BAML), taken **byte for byte** from the original exe. There is no readable XAML: changing how a window *looks*
  means decompiling these first, or changing the C# that builds the controls.
* `*.baml`, `app.ico`, `assets/` - the same layouts/icon as loose files, kept for reference (the project embeds `ModSwap.g.resources`, not these).

## What was changed from the 2.13.0 decompile
* build fixes only: target `net8.0-windows` + `RollForward LatestMajor` (as the original), `((Vector3D)(ref x)).Y` -> `x.Y`, `Duration.op_Implicit(t)` -> `(Duration)t`,
  `base.OnStartup/OnSourceInitialized/OnDrop`, `System.IO.Path`, `new Vector3D(...)`, no `RefSafetyRules` attribute.
* behaviour: **a game is never marked "can't edit yet" for good any more** (`MarkBroken` no longer writes `%APPDATA%\ModSwap\broken.txt`, `LoadBroken` ignores an old one).
* version 2.14.0.

## Checked here (Linux, no Windows)
* builds with 0 errors; published exe is a normal single-file bundle (ModSwap.dll + runtimeconfig + deps), `runtimeconfig.json` identical to the original;
* the rebuilt DLL has exactly the same 293 methods, 317 fields and 549 string literals as the original, and the same window layouts.
* NOT checked: starting it. WPF only runs on Windows, so nobody has run this build yet.

## Build (Windows, .NET 8 SDK)
    dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o publish
(on Linux add `-p:EnableWindowsTargeting=true`; the result only runs on Windows)
