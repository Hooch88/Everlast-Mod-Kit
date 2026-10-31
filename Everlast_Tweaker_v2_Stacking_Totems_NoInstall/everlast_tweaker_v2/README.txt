EVERLAST TWEAKER v2.0 — STACKING + PURIFICATION TOTEMS ONLY

No Python, BepInEx, .NET, or other installation.
Double-click START_EVERLAST_TWEAKER.bat (or open Everlast_Tweaker.html in Edge/Chrome).
Internet is required to load the sql.js SQLite engine from a CDN.

1. CLOSE Everlast, including its local server.
2. Click Load SQLite Engine.
3. Browse for:
   CLIENT: Everlast\Assets\Database\Definitions\ItemDefs.db
   SERVER: Everlast_Data\StreamingAssets\Server\Windows\Raptor.Data\Raptor.Game.db
4. Default stack size 99 and totem strength 2x. Adjust if desired.
5. Preview changes.
6. Click Download Original Backups to save copies of both input files.
7. Click Prepare Modified Databases, then Download Both Files.
8. Copy downloaded ItemDefs.db and Raptor.Game.db to the respective game folders, replacing the originals.
9. Back up your Worlds folder before testing; try cheap items first.

WHAT THIS EDITION DOES NOT MODIFY:
- Routine Curse gain, condition definitions, the occult system, ComponentSetDefs.db.
- Pouch capacity, 120 backpack slots, character/world saves.

This tool edits the selected database copies in browser memory; it NEVER writes directly to your game files.
Stacking rules use heuristic exclusions, not a guarantee about every item.
Totems are set from the known original base (-15/-30/-45/-60) rather than multiplied from their current value.
If a future developer patch changes base totem values, inspect the preview and update the tool before applying.
The client and local server may behave differently in multiplayer; designed for local/single-player files.
Database integrity is checked before generating output, but in-game functioning has not been validated.
