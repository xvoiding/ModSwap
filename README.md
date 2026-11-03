ModSwap
=======
Run ModSwap.exe. That's it.

1. Scan Steam (or Add game). Your games show up as tiles on the main screen, pick one.
2. Pick a character, drop in a model (file, folder or .zip) + textures.
3. Line it up against the original outline in 3D. Click any number to type your own value, there are no limits.
4. Install. Undo removes it any time.

Needs the .NET 8 Desktop Runtime (Windows offers to download it if you don't have it).
Only Unreal Engine games can be swapped for now. Log: %APPDATA%\ModSwap\modswap.log

## New in 2.3
- **Unlimited** checkbox: tick it and every slider keeps growing as you drag it to the end, up to 1000. You can also type any number into the value (up to 1000).
- **Edit body parts**: arms, legs, head and torso are found automatically. Pick one, then move it, resize it, tilt/turn/lean it, or tick Hide to delete it. Use the Box or Cut line tool to make your own part (like a tail or a hat), drag in the 3D view.
- **Your mods**: click a game and you see the mods you made for it. Install, uninstall, save a copy of the .pak, or delete. "Save for later" builds a mod without putting it in the game.

## New in 2.4: Unity games
ModSwap now also swaps models in Unity games (tested on ClusterTruck, Unity 5.3 Mono). Pick the game, pick the model to replace
(search the list, "trucks > load" is a whole truck), drop in your model, fit it, Install. The original file is backed up and
Undo / Delete puts it back byte for byte.
Works for models whose game files keep their type info. Games that keep everything in AssetBundles (data.unity3d) and
very new Unity versions are not supported yet.
Saved Unity mods are ".modswap.zip" files (your model + how it was fitted).

## New in 2.5: rigged characters in Unity games
Characters with skeletons (the player, NPCs, enemies: Trump in Mr. President!, Granny, Rick ...) now show up at the TOP of the model list
and can be swapped. Your model is auto-rigged onto the character's own skeleton, so the game's animations move it. The
body-part editor (move / resize / hide arms, legs, head) works on them too. The character's clothing and eye meshes are emptied
and its texture is replaced. If a game's character skeleton is not a humanoid (a rat, a spider), your model is skinned to the nearest bones instead.
Known limits: some games only put the upper body on the main mesh (legs/shoes are separate pieces), so the legs of your model follow the
thigh bones and do not bend at the knee; characters that share a mesh with other characters change all of them.

## 2.5.2
Fixes "No module named 'fmod_toolkit'" / 'archspec' when installing a Unity mod (missing libraries in the Windows runtime). Extract the zip to a normal folder before running it.

## 2.5.3
Models made of loose pieces (Baldi, low-poly / "kit" characters) no longer come out as shards. ModSwap now detects which parts of your model are
connected: a small loose piece (head, eyes, hair, hat, a hand) moves as one solid unit on the bone that owns most of it, instead of every vertex
being pulled toward whatever bone is nearest. Big connected pieces (a whole body, a leg) still bend as before. Also fixed: T-pose models were
guessed to face sideways (arms mistaken for the front), which sent hands flying off. If a model still faces the wrong way, set Forward by hand.

## 2.6.0
Cleaner model list for Unity games. ModSwap now sorts every model it finds: people and creatures, vehicles, weapons and objects are shown; whole
levels / map chunks, walls and floors, trees and rocks, repeating tiles, primitives (Cube.001, Plane) and machine-named meshes are hidden behind a
"Hidden" chip (they are not deleted). Models with useless names get a name from their parent or mesh instead. Duplicates across levels are merged.
New People / Vehicles / Weapons / Objects chips above the list, a small tag on each row, and search now looks through everything, hidden included.
The first scan after updating takes a bit longer because the list is rebuilt.

## 2.6.1
"could not restore ... (WinError 32)" now waits for the game to let go of its files and, if it doesn't, says plainly: close the game completely (Task Manager) and press Restore / Install again. Clicking a category chip now selects its first model.

## 2.7.0
"This game's character files use a newer format" - fixed for more Unreal games.
- Unreal 4.26+ cooks (GTA III Definitive Edition and similar) are now understood: ModSwap works out each game's mesh layout instead of assuming one of two.
- Characters whose skeleton is not a human (fish, head-only meshes, SpongeBob-style "jt_" rigs) no longer fail: your model is scaled into the original's
  footprint and skinned to the nearest bones.
- Unreal 4.23 skin-weight layout (SpongeBob SquarePants: Battle for Bikini Bottom Rehydrated) is supported in the engine, but it has only been
  checked against my own writer, not against the game's real files or in-game. If it still says it can't read a game, ModSwap now saves a
  report (layout_report.txt in %APPDATA%\ModSwap\cache\<game>\) and shows its path - send me that file and that game gets added.
- Games marked "can't edit yet" by an older ModSwap are tried again after updating (that list used to be permanent).
- Looks at several of a game's meshes before giving up, not just the first.
Not tested in-game: GTA III (only the head meshes were available to test).

## 2.8.0
SpongeBob SquarePants: Battle for Bikini Bottom - Rehydrated (Unreal 4.23) character files are now read and rebuilt. This is based on the game's real
mesh files (the Bikini Bottom fish), not a guess: ModSwap reads the whole mesh, swaps your model in, hides the old pieces and re-reads its own result
to check it. Characters with morph targets (Patrick and others) are handled by emptying those, which has NOT been checked against a real file.
Not tested in the game itself yet. Games marked "can't edit yet" by an older ModSwap are tried again after this update.

## 2.8.1
Fixes SpongeBob showing up as a grey banana. The game's SpongeBob body mesh is called "Spongebob_mesh" (no "SK_" in front), so ModSwap never saw it
and offered his tongue (which shares his skeleton) as "SpongeBob". ModSwap now also treats any asset that has a "<name>_Skeleton" or
"<name>_PhysicsAsset" next to it as a possible character mesh, then checks it by reading its header. Tongues, moustaches, teeth, eyes, lashes and
brows count as layered parts (hidden, not swapped). The first launch after updating re-scans the game once.
Also: two things asking for the repak tool at the same moment no longer fight over downloading it ("Permission denied" on repak.exe).
Still not tested in the game: SpongeBob's body has morph targets, so this is the first real test of that path.

## 2.8.2
Fixes swapped SpongeBob (Unreal 4.23) characters showing up covered in coloured noise. The old 4.23 cook stores the position of each texture level
relative to the package's bulk-data start, and ModSwap wrote plain positions, so the game read the texture from the wrong place. ModSwap now
detects which convention a game's own textures use and writes the matching one. Other Unreal games (Goat Simulator 3, Just Die Already, GTA III)
use the plain convention and are unchanged.

## 2.9.0  (DRAGON BALL: Sparking! ZERO, step 1)
ModSwap told you Sparking Zero's files "may be encrypted or in an unsupported pak version". Reading the game's real files, the first half of that
was true and the rest was a guess:
- All 20 of its .pak files are normal pak v11, but their file lists are **encrypted**. ModSwap now knows how to use an AES key, checks it against
  the game's own files before trusting it (a wrong key is rejected), and passes it to the pak tool. The key for Sparking Zero was checked against
  your real paks. You can add a key for another game in `%APPDATA%\ModSwap\keys.json` ({"steam-<appid>": "0x..."}).
- One unreadable pak no longer blocks the whole game, and errors now name the file.
- The real blocker: all the characters live in **IoStore** containers (.utoc/.ucas). The paks only hold audio, video, shaders and configs (checked:
  5,518 files in the main pak, none of them .uasset). ModSwap can't open IoStore yet, so it now says exactly that.
- Mods for this game are installed into `Paks/~mods` and need the "UTOC Signature Bypass" patch the community uses. ModSwap doesn't do that yet.
NOT done / not tested: reading IoStore, the UE5.1 skeletal-mesh layout, installing to ~mods. The 2.9 version also clears the old "not supported" mark.

## 2.9.1
Fixes "[WinError 2] The system cannot find the file specified: ...\Paks\zz_ModSwap_<old mod>_P.pak" when installing a mod. ModSwap had remembered
one of its own earlier mod files as if it were part of the game, and crashed looking up the size of that file after it was removed. It now checks
the game's pak list against what really exists every time, never counts its own mod files as game files, and says plainly if the game has no
readable paks. Nothing about the swap itself changed.

## 2.10.0  (Sparking Zero actually swappable + a mod-files manager for everything else)
**DRAGON BALL: Sparking! ZERO (UE5.1, IoStore)**
- ModSwap reads the IoStore containers through [retoc](https://github.com/trumank/retoc) (v0.1.5, downloaded once, checked against its sha256) with the
  game's AES key. The 303 characters show up with the names players know (read from the game's own text files), not file ids.
- Swapping works on the UE5.1 body meshes. Bodies that carry baked vertex colours / face morphs (about half of them) are now supported too:
  those extras are dropped from the new body (the shape is what you see, it just has no baked colours/morphs). All the other parts of the
  character are hidden so your model isn't wearing the old one.
- The result is packed to a container (.utoc/.ucas/.pak) and installed into `Paks/~mods`. Undo / "Reset everything" removes it.
- The game checks container signatures. You need the community **UTOC Signature Bypass** (dsound.dll in `SparkingZERO/Binaries/Win64`, from the
  game's Nexus Mods page) or the game ignores the mod. ModSwap tells you this after installing.
- NOT done: textures for UE5 games (the new model is shape-only, grey/default material for now), anything verified in the running game.
  Everything above was tested on your real game files up to "container built and verified by retoc", not by launching Sparking Zero.

**Mod files** (new button): for games where you can't just swap a model, drop in a downloaded mod (a .zip, a folder, or loose .pak/.utoc/.ucas/dll/ini/cfg files).
ModSwap works out where they go, backs up anything it overwrites, and can switch them off or remove them again.

**Easier for new users**: finds games from Steam, Epic, GOG, Xbox/Game Pass and Ubisoft; refuses to touch a game while it's running; plain-English
error messages; a "Reset everything" button that puts the game back like it was.

**Fixed**: the repak tool needs `--aes-key` before the command (newer repak versions refused it the old way). The 2.10 version also clears old
"not supported" marks.

## 2.10.1
- **Fixed: your model not showing in the preview for some characters** (e.g. Daddy's "Father"). That character's skeleton sits far below the ground
  line, and ModSwap's auto-rig assumed every skeleton starts at height 0, so it found no body to line up against and every vertex of your model
  came out as "not a number" (invisible). It now measures from the character's own feet. Checked on your real Daddy files: Father went from NaN to a
  normal fit and the mod builds. If a fit ever does come out invalid, you now get a clear message instead of an empty viewer.
- **Preview textures**: the preview atlas is now a PNG (no JPEG smearing) and the preview reloads when any texture file changes, not only the model
  file. I could NOT reproduce "preview textures look wrong but the installed ones are fine": the UV/atlas math checks out against the source
  textures, so if it still happens, send me the model + which character it was on.
- **Fixed: scrambled textures / fat-looking body in the 3D preview** (the model was fine, the picture was wrong). The viewer's camera used a clip range
  of 1 to 8000, and WPF's 3D depth buffer is too coarse for that: the back of the model (back of the shirt, the jeans) showed through the front,
  which looked like patchwork textures and a bloated body. The camera now keeps its near/far planes tight around the character. I checked your
  exact model (`Samba Dancing (5).fbx` + cssmoke.png) in the engine: the fitted shape and UVs are correct, so what installs in the game was never
  affected. I could not run the Windows viewer itself here, so this fix is NOT verified by eye.

## 2.10.3
- **Fixed: your custom model coming out with flat/low-res textures** (all four materials turned into 64x64 colour blobs). When the same texture had been
  dropped more than once, e.g. `hair_difa.png`, `1_hair_difa.png`, `textures__hair_difa.png`, ModSwap thought the match was ambiguous and gave up on
  it. It now treats copies of the same texture as one texture and picks the original. Checked on the exact files in your upload folder: skin, sweater,
  hair and pants all get their own 1024px texture again.
- Still open: the auto-rig makes Father (Daddy) look bloated at the hips and chest. It is the fit, not the viewer. I found where it comes from
  (arm bones are swung out and the shirt follows) but haven't fixed it yet.

## 2.10.4
- **Your model is no longer auto-bent to match the character.** Before, ModSwap moved your model's arms/legs toward the character's pose, which could stretch an arm or bloat a body. Now it just scales and places your model and keeps its own shape exactly.
- If your model's limbs sit in a very different pose than the character (e.g. T-pose vs A-pose) and you want the old behaviour, tick **"Match the character's pose"** in the fit sliders. Off by default.
- Heads up: with it off, the skeleton still drives your model in-game, so if the model's own pose differs a lot from the character's rest pose, limbs can look a little off while animating. Use the sliders/rotate or tick the box then.

## 2.11.0 - Marketplace
- New **Marketplace** button on every swappable game's page. It lists ready-made models; pick one, press **Use this model**, and it loads into the normal swap screen (choose the character, tweak, Install). No model site, no downloading by hand.
- Search, filter chips (All / This game / categories), pictures, size and author on every card.
- Adding models is just dropping them in: a folder (model + textures), a .zip, or a single .glb into the `marketplace` folder next to ModSwap.exe (ships with the app) or into the folder the **Open my models folder** button opens (survives updates). The name you give the folder/zip is the name shown. Optional `preview.png` and `info.json` (author, tags, category, games).
- Online catalog: `python -m modswap market build <folder> --out catalog_out --base-url https://...` turns a folder of models into a `catalog.json` + zips you can host anywhere; point `%APPDATA%\ModSwap\market.json` (`{"urls": [".../catalog.json"]}`) at it and the models show up for everyone, downloading on click. If the catalog is offline the last saved copy is shown. Online entries can only link to web addresses, never to files on the PC.
- Full instructions: `marketplace\README.txt`.
- Verified here: listing, previews, folder/zip/single-file models, copying into the swap screen, catalog build + offline/online rules, and the engine endpoints end to end (tests/test_market.py). The Windows page itself compiles but I couldn't open it, so the look is unchecked.

## 2.12.0 - Sketchfab in the Marketplace
- The Marketplace now has two tabs: **ModSwap library** and **Sketchfab**. On the Sketchfab tab you can search every downloadable model on Sketchfab (Popular / Newest / Characters / Vehicles / Weapons, or type anything) and press **Use this model** to load it straight into the swap screen. **View** opens its page on Sketchfab.
- Searching needs no account. **Downloading needs your own free Sketchfab API token**: press *Get my token*, copy the "API token" from that Sketchfab page, paste it into ModSwap and press Connect (one time). It stays on your PC (Windows encrypts it for your user) and is only ever sent to api.sketchfab.com. *Disconnect* removes it.
- Sketchfab's glTF downloads are converted to a single .glb so the textures always come with the model.
- Licences: each card shows the author's licence. Most are Creative Commons: *Attribution* means you must credit the author if you share your mod; *NonCommercial* means no selling. ModSwap writes a line for every model you use to `%APPDATA%\ModSwap\sketchfab_credits.txt`.
- Verified here with a fake Sketchfab: search mapping, token check/storage, glTF zip -> loads with its texture, credits file, errors (tests/test_sketchfab.py). The live search response shape was checked against the real API. Downloading from the real site needs a token, so that exact step is untested.

## 2.12.1
- **Fixed: installing a second mod in a Unity game failed with "Close <game> completely first... it still has sharedassets1.assets open".** The game wasn't the problem: ModSwap itself kept the first mod's backup file open after building the next mod, and Windows won't let a program delete a file that is still open. ModSwap now closes every file it read before it swaps mods, and a leftover backup copy can no longer block an install or restore.
- Tests: installing three mods in a row, then Uninstall, then reinstalling, in both a static-mesh game and a skinned-character game, with Windows' "can't delete an open file" rule emulated (tests/test_unity_two_mods.py, test_unity_two_skinned.py). Before the fix the leftover backup couldn't be removed; after it everything passes.

## 2.13.0 - install as many mods as you want
- Before, installing a mod first took out whatever was installed, so a game could only have one. Now mods **stack**: Baldi on one character, Big Smoke on another, a third on a third, all at the same time, in Unity and Unreal games.
- On **Your mods**, every card has its own Install / Uninstall. Uninstalling one leaves the others on. **Undo** after an install only removes the mod you just installed. Deleting an installed mod takes just that one out.
- If you install a new mod for a character that already wears another of your mods, the new one replaces the old one for that character (the old one stays saved in Your mods).
- Unity: a new mod is added on top of the game files as they are right now; uninstalling one puts the originals back and re-applies the others from their saved recipes (takes a few seconds per remaining mod). The panic button / "Put the game back to normal" still removes everything.
- Unreal / IoStore: each mod is its own patch pak, nothing already installed is touched.
- Tests: three skinned mods installed on different characters at once (both characters carry their model at the same time), remove one, replace one, reinstall from the library, delete one, restore everything (tests/test_unity_stack.py), plus Unreal pak/IoStore stacking (tests/test_unreal_stack.py).

## 2.14.0 - sliders, no vertex limit, reopen a mod
**Sliders no longer fight each other.** Turning the model changed which way "lean" leaned, and Width/Depth skewed the model once it was turned. Cause: the fit
turned the model first, then tilted it around the fixed world axes, then stretched it along the world axes. The order is now size (along the model's own
axes) -> lean/tilt about the pelvis -> turn about the vertical axis LAST -> move. Turn only spins the result, Width/Depth/Height only stretch it, and Height
no longer changes the tilt. (`tests/test_fit_sliders.py` runs the old order and the new one through the same checks: the old one fails them, the new one passes.)
Applies to Unreal and rigged Unity characters. Static Unity models and the body-part editor already worked in this order.

**No vertex limit.**
- Unreal: meshes with 65,536+ vertices are written with 32-bit indices instead of stopping with "mesh has too many vertices... decimate first".
- Unity 2017.3 and newer: same (32-bit index format).
- Older Unity (5.x, e.g. ClusterTruck): 65,535 vertices per mesh is a hard limit of the engine itself, so a bigger model is merged down to fit and the log says
  "reduced from N to M vertices" instead of failing. Nothing can draw more than that in those games.
- NOT verified in a running game: there are no Unreal game files here, only synthetic meshes checked with ModSwap's own reader. If a game rejects a big mesh, send the log.

**Reopen a mod you made (engine side).** Every mod now keeps a copy of the model, its textures and all fit settings (character, Forward/Up, size, sliders,
body-part edits, chosen parts). `POST /api/mod_edit {game, id}` copies them into a fresh upload and returns the settings so the fit screen can restore
everything. Mods made before this version don't have the copy: it says so and you make them again once. The "Edit" button itself has to be added to the
Windows app.

**Missing characters (SpongeBob / Patrick / Sandy).** Two changes, neither confirmed against that game's files:
- The scanner now also looks at meshes named `<Name>_mesh` / `<Name>_body` / `_skm` / `_model` that sit next to `<Name>_Skeleton` / `<Name>_PhysicsAsset`
  (before, the names had to match exactly, so `Patrick_mesh` was never even checked). Every candidate is still header-verified, so this can't add non-meshes.
  The first scan after updating is redone.
- Every scan now writes `scan_report.txt` next to the game's cache (`%APPDATA%\ModSwap\cache\<game>\`): which meshes were found, which were dropped and why, how
  they were grouped into characters, and which mesh-looking files were never looked at. If a character is still missing, that file shows why.

Not in this version: Spider-Man (Insomniac engine), Sonic Frontiers / Sonic Colors (Hedgehog Engine). These engines have no support in ModSwap.

**Just Die Already shows "not supported" / "mod files only".** Not the engine: the Windows app keeps a permanent list of games that once hit an error (a pak that
repak couldn't open, "no .pak files", "not supported yet") in `%APPDATA%\ModSwap\broken.txt` and greys them out for good, whatever the engine says. The file
also keeps the original error text. Delete it (close ModSwap first) and the game is tried again. The engine side now also ignores a stale "supported: false" in `games.json`.
Making the app stop doing this needs a change in its C# (see `ui-recovered/`).

**More for SpongeBob-style games.** A mesh package whose SkeletalMesh is not export 0 (characters with face morph targets have extra MorphTarget exports) is now
recognised (before only export 0 was checked, which would drop exactly such characters). Main/player characters are listed first, props last, and `_mesh` is
dropped from names. Not confirmed against the game's files. Also found in the layout report: `SK_Fish_Beach_01` has cloth data, which the reader still refuses.

**ModSwap.exe is rebuilt (2.14.0).** Its source is now in `ui-recovered/` (see `RECOVERY.md`). The only behaviour change: a game is never greyed out "for good" after one error
(the `broken.txt` list is gone). Everything else matches the old exe (same methods, same text, same window layouts), but this build has not been started on Windows yet.
The previous exe is still in git history: `git checkout fc67f9e -- ModSwap.exe`.

## 2.14.1 - texture fixes + rebuild your mods
Swaps work in SpongeBob and Just Die Already, but the new model's textures looked wrong in the game (flat white in SpongeBob, blurry/smeared in JDA).
What was checked and what changed:
- **Checked and fine:** BCn compression (colours, channel order, alpha) and the atlas/UV mapping (median error 0 of 255, with tiled UVs). The picture ModSwap makes is right.
- **Found and fixed (real bug):** when the character's ORIGINAL texture has no separate `.ubulk` data (small or never-streamed textures, every mip inline), the old writer put the
  big mips in a `.ubulk` but flagged them as inline, so the game could not read them. Now an all-inline template keeps every mip inline. (`tests/test_texture_writer.py` runs the
  old and new writer on the same fake templates: the old one produces an unreadable file for the all-inline case, fine for the other two; the new one is clean in all three.)
- **Every texture is now read back after it is written** (mip sizes, flags, payload positions, header pointers, the pixels in the .ubulk). If anything is off, the build stops with
  a clear message instead of installing a broken mod.
- **Texture names:** a texture called ...Default / ...White in the character's OWN folder (JDA's `T_WallyDefault_BC`) is its real texture, not a placeholder. It used to be thrown away, which
  left the original picture on the new model (wrong colours in the wrong places).
- **BC3 alpha:** a DXT5 colour texture now keeps the original's alpha level instead of forcing 255 (some games use alpha as a glow/mask, which would whiten the model).
- **`texture_report.txt`** (in `%APPDATA%\ModSwap`) is written on every build: which textures were replaced or skipped and why, their format / size / mips / flags in the original and in
  the mod, whether the read-back check passed, and the colour of your model's atlas. If textures are still wrong, that file says why.
- **Rebuild without remaking:** `runtime\python.exe -m modswap rebuild` redoes every saved mod that kept its model (made with 2.14 or newer) with every setting exactly as before,
  and installed mods stay installed. Mods made before 2.14 only have the finished file: make those once more.
NOT verified in a running game. Which of the above was the cause for SpongeBob / JDA depends on those games' texture files, and the report will show it.

## Next: Spider-Man and Sonic Frontiers (in progress, nothing swappable yet)
Studied from the real game files (sample zips via `tools/collect_samples.py`):
* **Sonic Frontiers** (build 16857613): every archive is `PACx403L` (Hedgehog Engine 2 PACx v403, little-endian, LZ4-compressed root in 65,536-byte chunks, metadata block with parent list).
  Characters are in `image/x64/raw/character/*.pac` (sonic, sonic_birthday/crown/cyber, supersonic*, amy, tails, knuckles, big, eggman, sage, ...). Format reference: HedgeLib (MIT).
* **Spider-Man Remastered** (build 23986256): the whole game is ~2 GB archives (`g00s000`...) plus `asset_archive/toc`, a zlib-compressed `DAT1` index of 771,677 assets
  (`modswap/insomniac/toc.py`, my own reader, checked against the real file: ids, sizes, archive + offset; asset id = CRC-64/XZ-style hash of the lower-cased path).
  The classic suit is `characters/hero/hero_spiderman_classic/hero_spiderman_classic.model` (11 MB, original in `g00s001`). The earlier ModSwap test mod redirected it to
  `asset_archive/mods/modswap_test` by adding an archive entry to the toc (a 96-byte-smaller copy of the original), which is how Spider-Man was swapped before.
* `tools/collect_spiderman.py` pulls the original suit model and everything it references (materials, textures) plus the earlier mod, `tools/collect_samples.py --include/--only` pulls named archives whole.
UPDATE (second sample round):
* **Spider-Man archives are `DSAR` block-compressed** (`modswap/insomniac/archive.py`): a block table from byte 32 (u64 decompressed position, u64 compressed position, u32 decompressed size 262,144,
  u32 compressed size, u32 flags, filler), blocks are LZ4. The toc's asset offsets are positions in the DECOMPRESSED stream, which is why some lay past the end of the file (the first collector read the
  wrong bytes). Checked on three real archive headers. The earlier mod's archive (`mods/modswap_test`) is a plain, uncompressed asset: 36-byte header, then a `DAT1` block (type 0x98906B9F, 29 sections).
* **Sonic Frontiers archives are readable** (`modswap/hedgehog/pacx.py`, verified on the real amy / tails / knuckles / sonic / playercommon .pac): outer `PACx403L` -> LZ4 chunk table -> inner `PACx402L`
  root -> its dependency table names the embedded split (`amy.pac.000`, another LZ4-chunked inner archive) that holds the real data. amy.pac.000: 1 `model` (3.2 MB, magic `NEDARCV1`), `material`s,
  `uv-anim`/`mat-anim`; sonic.pac: 4 models, 35 DDS textures (1024x1024 BC1/BC5/BC7 with full mip chains). Amy's own colour textures are not in her split (probably her parent archives).
NOT done: reading the model contents (NEDARCV1 / Spider-Man `.model`), writing a new model, writing a PACx / patching the Spider-Man toc, installing, Sonic Colors. ALERT (Tkachov) documents the Insomniac formats but is GPL-3.0, so nothing is copied from it.

### Spider-Man, third round (real extraction now works)
* `tools/collect_spiderman.py` now reads the game correctly (DSAR blocks): the original classic-suit model and its 11 materials came out clean (all `DAT1`). Materials name their
  textures by PATH TEXT (`characters\\hero\\hero_spiderman\\textures\\..._n.texture`), so the toc reader/collector also follow path strings (78 of 88 strings in the real materials resolve).
* `modswap/insomniac/model.py` reads the model's section table and standard vertex stream (XOR-delta, 8 planar int16 streams per batch, 1/4096 m): the classic suit decodes to 179,334 vertices,
  1.82 m tall. Section tags: index 0859863D, standard verts A98BE69B, uv1 6B855EED, colour 5CBA9DE9, joints 15DF9D3B, ...
* **What the earlier test mod did:** it kept every one of the 29 sections at its original size and only rewrote the contents of the index buffer, the standard vertices and a few small tables,
  i.e. it reshaped the SAME 179,334 vertices instead of writing a model of a different size. That explains the odd figure and why textures were not touched.
NOT done: index buffer / mesh table / skin-weight decoding, writing a model with a new vertex count, toc patching + archive writing, textures (.texture format), installing.
