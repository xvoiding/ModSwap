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

## 2.14.2 - one unreadable character no longer hides a whole game
Just Die Already showed "ModSwap can't read this game's character files yet" after the 2.14 update, although it had worked before. Cause: the game's mesh layout was detected only from the
files of the character being fitted, and the list now puts main characters first, so the first character (which the app fits your model onto automatically) was one whose files do not parse;
the app then treated that single failure as "this whole game is unreadable" and hid the list. Now, when none of a character's own meshes parse, the layout found on the game's OTHER characters
(or on an earlier success, kept in `format.json` in the game's cache folder) is used. The "can't read" message only appears when no character of the game can be read at all. (`tests/test_game_format.py`)
Known and still open: a few meshes carry cloth data (`cloth mapping data present`), which the reader refuses; those characters will still fail when fitted, with a normal error message.

## Spider-Man: command line for a first in-game test (mesh + rig, NO textures yet)
```
python -m modswap spiderman suits
python -m modswap spiderman slots --suit classic
python -m modswap spiderman install --suit classic --model my.fbx --name Test        (game closed!)
python -m modswap spiderman list
python -m modswap spiderman restore                                                  (game exactly as before)
```
* The new suit model is written in the game's own format (verified by reading it back, and by re-encoding a real suit byte for byte), the character is auto-rigged onto the suit's 212-joint skeleton, and the game's index (`asset_archive\toc`) is redirected to it. The original index stays as `toc.BAK`; `restore` copies it back and deletes the mod files.
* Material slots: mesh part k uses material record k (found by reading the model; the old note "slot 7" was wrong, the rubber material is slot 3 on the classic suit). Every part is put on the plain colour+normal+gloss slot.
* **Textures (new):** the suit's colour / normal / gloss textures for the chosen slot are replaced (`.texture` = 36-byte header + 92-byte DAT1 + BC7 mips; format worked out from 60+ real textures, every pixel size reproduced; `modswap/insomniac/texture.py`). Your picture goes in as a 1024x1024 BC7 colour map (`--tex-size 2048` for more), the normal map becomes flat and the gloss map neutral. Check: the written texture sampled at the written model's UVs gives the right colour on 100% of vertices; re-encoding a real texture gives 55 dB PSNR. `--no-textures` leaves the suit's own picture.
* **Verified in the game by the owner:** mesh + rig (a custom model stands, poses and animates as Spider-Man). The auto-detected facing was wrong for one FBX: pass `--forward +X` / `-X` / `+Z` / `-Z` or `--yaw 180`.
* **Not verified in the game:** the replaced textures (stored size 1024 where the original stores 512 of a 2048 texture; the format field codes were copied from the original, only size fields change); `--flip-v` is only needed if a picture comes out upside down. Sonic Frontiers is not swappable yet.

## 2.15.0 - Spider-Man in the app + a model-viewer texture fix
* **Spider-Man Remastered is a normal game in the app now** (no command line needed): it is detected as "Insomniac Engine", its suits are the characters, the 3D viewer, sliders, Up/Forward options, "edit a mod", the mod list (install / uninstall / stack) and "Put the game back to normal" all work like for the other engines. A game saved earlier as "unknown engine" is fixed automatically. The command line (`python -m modswap spiderman ...`) still works.
* A mod = the suit's model + its three textures (colour = your picture at 1024x1024, flat normal, neutral gloss). A new mod for a suit that already wears one replaces it. Tested end to end through the app's own server functions on the real suit assets (fit for the viewer, apply, replace, uninstall, reinstall from the library, restore byte for byte).
* **Viewer / texture bug fixed:** loaders welded vertices by position + normal + uv but NOT by material, so a vertex shared by two materials (typical where a head meets a body) could map into only one material's part of the texture atlas and the other material's triangles smeared across the wrong part of the picture. Vertices are now split per material (`modelio.split_by_material`, test: `tests/test_material_split.py`). I could not look at your viewer; if textures still look scrambled after this, a screenshot of the viewer next to the same model in-game would pinpoint it.
* Not verified: the app screens themselves with a real Spider-Man folder on your PC (the server functions are tested; the WPF app is unchanged).

## Sonic Frontiers: the model format is now read (nothing is swappable yet)
* `modswap/hedgehog/needle.py` reads / rebuilds the `NEDARCV1` container of a `.model` (byte-identical rebuild of Amy's file) and `modswap/hedgehog/hemodel.py` reads a `NEDMDLV5` model:
  all 89 meshes of Sonic, Amy, Knuckles and Tails (every level of detail) decode: positions, 10-bit normals / tangents, half-float UVs, vertex colours, skin bone indices + weights, the
  triangle lists, material names, texture slots, and the 140-190 node skeleton (names, parents, inverse-bind matrices -> bind-pose positions).
* Checked: every position is finite and inside the model's stored bounding box, normals are unit length, skin weights sum to 1, bone parents come before children, Hips sit at mid height
  with Head above and the ears on opposite sides, and a render of Sonic's vertices coloured by their dominant bone shows head, ears, arms, gloves and shoes where they belong.
* Format notes (worked out on the real files; HedgeLib, MIT, documents the Sonic Forces version of the same structures): counts / sizes / floats / vertex data are BIG endian; pointers are
  little-endian values relative to their own address (inside a Needle archive) or big-endian offsets from byte 0x10 (a bare chunk). Mesh part = 0x2C bytes (material, faces, vertex count,
  vertex size, vertices, vertex elements, bone table, texture units). Vertex = 40 bytes: float3 position, three 10-bit packed vectors (normal, tangent, binormal), half2 uv, 4 colour bytes,
  4 bone bytes, 4 weight bytes. Characters are drawn with extra OUTLINE meshes (toon edge) and a FUR mesh (the body), so a swap has to deal with those too.
* Not done yet: WRITING a model (the pointer table at the end of the chunk must be regenerated), writing the `.pac` back (LZ4 chunks, header sizes), replacing the DDS textures, the
  installer, and the app screens. Nothing here has been tried in the game.

## 2.16.0 - Sonic Frontiers can be swapped
**Verified in the game by the owner: Sonic swapped for a custom model (Granny) with its textures, no crash, no lag.** Amy, Knuckles and Tails (below) are built the same way but NOT yet tried in the game.
```
python -m modswap sonic characters
python -m modswap sonic install --character sonic --model my.fbx --textures FOLDER --name Test      (game closed!)
python -m modswap sonic list
python -m modswap sonic restore                                                                      (original .pac files back, byte for byte)
```
Also in the app: Sonic Frontiers is detected as "Hedgehog Engine 2", its swappable characters are listed, and the viewer, sliders, edit-a-mod, mod list, uninstall and "put the game back to normal" work like for the other games.
* **How a swap works.** The character's `.pac` is rewritten. The model is filled IN PLACE: the game's own mesh parts are slots with a fixed amount of room, the user's triangles go into them
  (vertex / index counts are lowered, the bone table is rewritten, data is written big-endian in the slot's own vertex layout), every other part (the toon OUTLINE shells, the fur, the eyes ...)
  becomes one degenerate triangle, and parts that have to share the plain `cloth` material re-point at its strings (pointers are self-relative and only ever written FORWARD, as in the game's
  own files). Nothing moves, so the pointer table at the end of the model and the `.pac` layout stay valid. The 3 textures of the cloth material (`_abd` diffuse BC1, `_nrm` normal BC5,
  `_prm` params BC7) are replaced by DDS files of exactly the same size and format: your picture, a flat normal map, a neutral params map. Then the `.pac` is written again: 64 KB LZ4
  chunks, the split's size / position patched in the root archive, header sizes (`pacwrite.py`; a `.pac` rewritten without changes reads back identical).
* **Checked on the real `sonic.pac`:** only the model and the 3 textures differ afterwards; the written model read back with the reader: positions exact, uvs within half-float precision,
  normals / tangents / binormals orthonormal (tangent = +u, binormal = -v, w bits 3, like the game's own), skin weights sum to 1, dominant bones preserved, triangle order and winding kept;
  the written diffuse texture sampled at the written uvs gives the right colour on 100% of the vertices; a model too big for a level of detail (the lower levels hold fewer vertices AND
  triangles) is reduced with a message; installer: backup, replace, uninstall, restore byte for byte; all of it also through the app's server functions on a fake Sonic folder.
* **Amy, Knuckles, Tails (new, untried in the game).** Their `.pac` keeps only 170-198 byte `NTSI` streaming stubs of the textures (the real pixels are in `texture_streaming\\character.ntsp`). The stub carries the
  texture's DDS header, so ModSwap writes a FULL texture of that size and format in its place (the same `.pac` already holds full DDS files next to stubs, so the engine takes both). The bigger file
  is appended at the end of the archive's file data (`innerwrite.py`: every pointer position of the archive lies in the front part, so only the offset table moves) and, when the split gets more chunks, its
  chunk table moves to the end of the root's file data (`pacwrite.py`). Only the model and the 3 textures differ afterwards (tested). Not looked at: Sonic's other forms (`soniccyber`, `supersonic` ...), the
  cyber-space texture variants (`*_cyb_abd`), Sonic Colors: Ultimate.
* **Confirmed by the Sonic run:** the game accepts the lowered vertex counts, the rewritten `.pac`, the hidden-parts trick and the cloth material on a whole body. Sonic's outline shell and eyes disappear (the user's model brings its own).

## 2.16.1 - big models no longer freeze the app, and the offset sliders are in real centimetres
* **Freeze fixed.** The 3D viewer builds its meshes on the app's UI thread, and Spider-Man's own outline alone is 216,594 triangles (the viewer also builds an edge mesh from every one), so changing the
  model / a slider froze the window ("Not responding"). The viewer now gets a reduced copy (`modswap/viewerlod.py`): the faint original at most 14,000 triangles, your model at most 90,000 (a 400,000
  triangle test model: 3 s per slider change). The reduction is planned once per model and cached; per-vertex data (uvs, body-part groups) follow the kept vertices. Builds NEVER use it: game files
  are made from the full-detail model. Applied to Unreal, Unity, Spider-Man and Sonic previews.
* **"Slide to 1, it jumps to 1000" fixed.** The Left/right, Forward/back, Up/down sliders (and the Edit-body-parts move / pivot values) are in centimetres, but the Spider-Man and Sonic rigs are in METRES and
  the auto-rig adds them in rig units, so 1 cm moved the model 1 m (10 cm moved it 1000 cm). They are converted now (`swap.metres`, `edit.scale_lengths`); tests move a model 10 cm and measure 10 cm on both
  rigs, and a part move of 10 cm moves only that part by 10 cm. Unreal and Unity were not affected (their rigs are in centimetres). Mods made before this with a non-zero offset slider should be re-made.

## 2.16.2 - texture diagnostic, texture-safe viewer reduction
* `python -m modswap diagnose --model my.fbx --textures FOLDER` loads a model like the app does and checks, material by material, that every vertex finds the right colour in the atlas the viewer and the builds
  use (1024 and 2048). It writes `diagnose_report.txt` (which picture each material got, its size and average colour, UV ranges, triangles whose corners mix materials, atlas mismatches), `atlas_1024.png`
  (the atlas with every material's cell outlined) and one preview picture per material. Use it when a model's textures look wrong in the viewer.
* The viewer-only reduction for huge meshes (2.16.1) now keeps vertices of different atlas regions apart (`viewerlod.labels_from_uv`), so a reduced triangle can never mix corners from different
  materials / UV islands and smear the texture over the model. Test: two texture regions on a big sphere, no reduced triangle spans both.

## 2.16.3 - textures: pictures in nearby folders, one cell for a shared picture
* The FBX loader looks for a material's picture by exact file name in the model's folder, its sub-folders and the sub-folders of the parent folder (`source\\model.fbx` + `textures\\x.jpeg`), not just next to the model.
* Materials that use the SAME picture (very common: one atlas texture for a whole character) now share ONE cell in the preview / build atlas (`atlas.pack`), so a model with twenty materials and one
  2048 texture keeps that texture at full detail instead of twenty shrunken copies.
* `python -m modswap diagnose --model MODEL_FOLDER` also accepts a whole model folder (finds the .fbx / .glb / .obj inside it).
* `tests/test_fbx_loader.py`: a Mario-like ASCII FBX (3 parts, 3 materials, one shared picture in `textures`, indexed per-corner UVs) checked against ground truth at 1024 and 2048.
* Still open: the exact cause of the scrambled-Mario viewer screenshot is not reproduced (all the above pass on synthetic models); the diagnose report from the real model decides.

## Repair: "Couldn't start the engine ... not a valid application for this OS platform"
`runtime\python.exe` (ModSwap's private Python) is damaged or missing (a zero-byte / truncated file, often antivirus or a failed copy). Put `Repair-Runtime.bat` and `Repair-Runtime.ps1` in the ModSwap folder and double-click the
.bat: it downloads the official embeddable Python 3.12 from python.org, installs pip and everything in `requirements.txt`, and keeps the old folder renamed as `runtime_broken_<time>`.

## 2.16.4 - the app now says what it is waiting for
* A job that has to wait for another running job (all jobs share one lock) now shows "waiting for another task to finish..." instead of looking stuck on "Reading the game files...", and every job
  starts with "starting ..." (the first run after an update / after rebuilding `runtime` compiles and virus-scans thousands of files and can take a minute).
* The engine writes `engine.log` into the ModSwap config folder (`%APPDATA%\\ModSwap\\engine.log`): when each job was queued, started, how long it waited, every log line it printed, and the full error if it failed.
  Send that file (and `%APPDATA%\\ModSwap\\modswap.log`) when something hangs.

## 2.16.5 - textures: every kind of textured model is now tested against ground truth
`tests/texmatrix.py` + `tests/test_texture_matrix.py` generate models whose colour at every triangle corner is known, write them as OBJ / GLB / glTF / Collada / FBX (ASCII and binary, 32 and 64-bit),
load them through ModSwap's real loaders, run the atlas the viewer and the builds use, and compare every corner with what the SOURCE file says; the viewer's own fit answer is checked the same way.
Bugs this found and fixed:
* OBJ: pictures in a sub-folder (`map_Kd textures/x.png`) were never found (the material turned grey); `-s 1 1 1`-style map options; a plain `Kd` colour when no picture; case differences; both now use
  the same nearby-folder search as FBX (`modelio.find_picture`).
* FBX: UV mapping `ByControlPoint` (the correct spelling) was unknown (every corner got one uv); texture wrap modes (repeat / clamp) were ignored.
* glTF / GLB: `baseColorFactor` tint, sampler wrap modes (repeat / mirror / clamp) and `KHR_texture_transform` were ignored.
* Heavy tiling (a uv range of +-60) or one stray uv (900, -700) made the atlas packer fail ("textures cannot be packed"). Tiled uvs are folded back per triangle (`modelio.normalise_tiling`), a clamped
  axis only needs 0..1, stray extremes are ignored for the cell size and clamped into it, and the packer can no longer fail.
* Pictures: 16-bit / float / palette / alpha / grey modes are converted properly (`to_rgb`); pictures over 2048 px are shrunk when read (twelve different 4096x4096 pictures: 4.7 s, 850 MB instead of
  several GB); a file used by many materials is decoded once; materials that share one picture share one atlas cell (full detail); NaN uvs are made harmless.
* Not covered: `.blend`, `.3ds`, USD, Alembic (they go through Blender, which must be installed), vertex-colour-only models (shown as their average colour), a second uv set.

### Spider-Man: more characters, and the `report` command
The game's index stores only hashes of asset paths, so ModSwap lists a character when its path is guessed from `modswap/insomniac/names.py` (every guess is checked against the real index, so only
models that exist show up): suits at `characters/hero/hero_spiderman_<id>/`, other characters (Mr. Negative, Kingpin, Rhino ...) at `characters/npc/npc_<id>/`. Suits whose material is not the plain
"colour + normal + gloss" kind fall back to their most-used material that has its own colour texture. `python -m modswap spiderman report [--suit punk] [--npcs]` writes `suits_report.txt`
(mesh table, materials, textures of every suit) for diagnosing a suit that looks wrong.

### Unity: models that lie down, and 2018+ vertex layout
* `modswap/unity/orient.py` finds which way is up for a Unity model: the rotation on its GameObject chain (a z-up export carries a -90 degree turn that stands it up in the game), checked against the
  skeleton for characters (head above feet). The viewer draws the model standing and the builder writes the new mesh back into the mesh's own space (rotation + the mesh GameObject's matrix).
* `patch.set_mesh` writes the vertex data in the layout of the game's Unity version: 8 channels (<= 2017, uv0 = channel 3) or 14 (2018+, tangent 2, uv0 4, blend weights 12, bone indices 13).
  Writing the old layout into a newer game put the uvs in the colour channel, so custom textures never showed (Megabonk).
