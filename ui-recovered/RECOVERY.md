# Recovered source of ModSwap.exe (2.13.0)

The Windows app's own C# source wasn't in the repo, so this was decompiled from `ModSwap.exe` (ILSpy 8.2: unpack the single-file bundle, then decompile `ModSwap.dll`).
It is **not a working build yet**.

* `ModSwap/*.cs` - all the UI logic (MainWindow, Api, Backend, Viewer3D ...), ~8,500 lines. Names of methods/classes are intact; local variable names are `val1, val2 ...`.
* `*.baml` - the window layouts, kept in their compiled form (the project embeds them as they are). There is no readable XAML: changing how a window *looks* means
  decompiling these first, or editing the C# that builds the controls.
* `ModSwap.csproj` - net8.0-windows, WPF.

Fixes already applied on top of the raw decompile: target framework `net8.0-windows`, `((Vector3D)(ref x)).Y` -> `x.Y` (113 places), removed the compiler-reserved
`RefSafetyRules` attribute.

Still failing to compile (25 errors on the last try, more may sit behind them): explicit `Duration.op_Implicit(...)` calls in `Anim.cs`, `base.OnStartup` access in
`App.cs`, an ambiguous `Path` (System.IO vs System.Windows.Shapes) in `MainWindow.cs`, and a few more of the same decompiler kind.

Build (Linux or Windows, .NET 8 SDK):  `dotnet build -c Release -p:EnableWindowsTargeting=true`
Nothing here has been run: WPF only runs on Windows.

Why it matters: `MainWindow.MarkBroken` / `LoadBroken` keep a permanent "can't edit yet" list in `%APPDATA%\ModSwap\broken.txt`.
