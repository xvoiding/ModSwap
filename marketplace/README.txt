MODSWAP MARKETPLACE  -  put models in this folder
==================================================
Everything you put in here shows up in the app under  <a game> > Marketplace.
Players click "Use this model" and it loads straight into the swap screen. No model site needed.

HOW TO ADD A MODEL (any of these)
  1. A folder:   Big Smoke\   with the model file (.fbx .obj .glb ...) and its textures inside.
                 The folder name is the name shown in the app.
  2. A .zip:     Big Smoke.zip   (model + textures inside, subfolders are fine).
  3. One file:   Big Smoke.glb   (only for formats that carry their own textures: .glb / .vrm)

OPTIONAL EXTRAS
  preview.png      a picture of the model (put it inside the model's folder). For a .zip, put "Big Smoke.png" next to the zip.
  info.json        inside the model's folder:
                   { "name": "Big Smoke", "author": "you", "description": "short text",
                     "category": "people", "tags": ["gta", "npc"], "games": ["Sparking Zero"] }
                   "category" makes the filter buttons. "games" puts the model first (and under "This game") for those games.

ONLINE CATALOG (so you can add models without re-sending the app)
  1. Run:  python -m modswap market build  <this folder>  --out catalog_out  --base-url https://your-site/models/
     (or with the bundled python:  runtime\python.exe -m modswap market build ...)
     It writes catalog_out\catalog.json + one .zip and one preview picture per model.
  2. Upload the whole catalog_out folder anywhere that gives direct links (a GitHub repo / release, your own website).
  3. Put the link to catalog.json in  %APPDATA%\ModSwap\market.json :
         { "urls": ["https://your-site/models/catalog.json"] }
     Models then appear in everyone's Marketplace and download when they click "Use this model".

Your own private models: use the "Open my models folder" button in the Marketplace page (that folder survives app updates).

SKETCHFAB
  The Marketplace page also has a Sketchfab tab (search + one-click use). Needs a free Sketchfab account and its API token, pasted once in the app.
