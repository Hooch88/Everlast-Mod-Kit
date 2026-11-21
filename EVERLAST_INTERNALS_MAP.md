# Everlast Internal Architecture & Modification Knowledge Map

> **Purpose:** Comprehensive, persistent reference mapping all files, database tables, schemas, IL2CPP structures, and exact binary patch offsets for Everlast. Eliminates the need for repetitive scans.
> **Game Directory:** `D:\SteamLibrary\steamapps\common\Everlast`
> **User Saves Directory:** `%LOCALAPPDATA%\InSpades\Everlast\Worlds\<WorldName> (Legacy: %USERPROFILE%\Documents\My Games\Everlast\Worlds\<WorldName>)`
> **Mod Kit Project:** `C:\Projects\GameMods\Everlast`
> **Verified against:** Everlast v0.13022.0 (Steam build 26670585). Byte offsets in section 3 are for this version only; see section 4 to port them after a game update.

---

## 1. Directory Structure & Key Files

| Relative Path | Format | Role & Contents |
|---|---|---|
| `Assets\Database\Definitions\ItemDefs.db` | SQLite | Definitions of all items, stack sizes, prices, categories, tags. |
| `Assets\Database\Definitions\ComponentSetDefs.db` | SQLite | Definitions of event/game components (Desolate zones, Altar/Shrine xp rewards, gathering timers). |
| `Assets\Database\Definitions\EstatePlotDefs.db` | SQLite | Definitions of estate plots, labels, upgrade requirements (`ItemsForUpgrade`). |
| `Assets\Database\Definitions\NpcDefs.db` | SQLite | Definitions of all NPCs/mobs, stats, and individual respawn timer (`DespawnedTime`, `CorpseFadeTime`). |
| `Assets\Database\Definitions\NpcGroupDefs.db` | SQLite | Definitions of NPC groups/packs and pack respawn timers (`RespawnTimeMs`, `RespawnTimeMaxMs`). |
| `Everlast_Data\StreamingAssets\Server\Windows\Raptor.Data\Raptor.Game.db` | SQLite | Server-side master database containing all definition tables (must stay in sync with client `.db` files). |
| `Everlast_Data\StreamingAssets\Server\Windows\Raptor.Game.exe` | PE AOT .NET | Dedicated server executable (hosts local/MP session; handles authoritative game logic). |
| `Everlast_Data\il2cpp_data\Metadata\global-metadata.dat` | IL2CPP v31 | Client type definitions, string literals, fields, method metadata. |
| `GameAssembly.dll` | PE x64 Native | Compiled IL2CPP native client code for all client assemblies. |
| `%LOCALAPPDATA%\InSpades\Everlast\Worlds\<World>\save\gen-0001.db (or gen-0002.db)` | SQLite | Player world save database (inventory, finances/merits, character skills). |

---

## 2. Database Tables & Mod Schemas

### A. `ItemDefs.db` & `Raptor.Game.db` (`ItemDefs` table)
- **Primary Key:** `Id` (INTEGER)
- **Key Columns:**
  - `Stackable` (INTEGER): `0` or `1`.
  - `MaxStackSize` (INTEGER): Default is 1, 5, 10, 20, 40, 100 depending on item category.
  - `Name` (TEXT): Display name.
  - `Categories` (INTEGER): Item category bitmask.
  - `Components` (TEXT / JSON): Item behavior components (e.g. `EquippableComponent`, `CurseGain`).
  - `ReplacedBy` (INTEGER): added in v0.13021.0; unused by the kit.
- **Mod Patch:** Stacking mod updates `Stackable = 1, MaxStackSize = 100` (or configured value) for resources and non-equipped items.

### B. `ComponentSetDefs.db` & `Raptor.Game.db` (`ComponentSetDefs` table)
- **Primary Key:** `Id` (INTEGER)
- **Key Rows:**
  - **Id = 135 (`Event-DesolateZone-Zones`):**
    - Component: `Raptor.Game.Components.Events.DesolateZoneComponent, Raptor.Game.Definitions`
    - Contains: `Locations[]` with `LocationProgressionReward` and `Stages[].CompletionZonePoints`.
    - **10x Boost Patch:** Multiply both fields by 10.0 for accelerated progression.
  - **Id = 136 (`Event-DropOff`):**
    - Component: `Raptor.Game.Components.Events.DropOffComponent, Raptor.Game.Definitions`
    - Contains: `CompletionZonePoints`.
    - **10x Boost Patch:** Multiply by 10.0.
  - **Altar & Shrine Exp:** There are no `ComponentSetDefs` rows 1130-1133 (an earlier version of this map listed them, but they never existed). Ichor and totem Occultism XP lives in `ItemDefs` (`ConsumableComponent.XpRewards`, items 148-151 and 1081-1084). Shrine multipliers live in `ComponentSetDefs` **Id 150** (`OcculticShrineComponent`: Domaanziin Shrine x2.0, Occultic Shrine x2.25).
    - **Exp Boost Patch:** Multiplied by 3x - 10x.
  - **Gathering Nodes (Ids 5, 12, 35, 40, 84, 85, 115):**
    - Contains `GatherableComponent` with `DepletionTimer` (ms before resource node respawns, e.g. 30,000–120,000 ms).

### C. `EstatePlotDefs.db` & `Raptor.Game.db` (`EstatePlotDefs` table)
- **Primary Key:** `Id` (INTEGER)
- **Key Column:** `Variants` (TEXT JSON Array)
  - Each variant object contains:
    - `VariantId` (INTEGER): 1, 2, 3...
    - `Label` (TEXT): Display name of building/upgrade.
    - `SelectableForUpgrade` (BOOLEAN): `true` if player can choose it.
    - `ItemsForUpgrade` (ARRAY): List of required item IDs and amounts, e.g. `[{"ItemId": 45, "Amount": 100}]`.
- **Free Estate Build Mod Patch:** Set `ItemsForUpgrade = []` across all variants.

### D. `NpcDefs.db`, `NpcGroupDefs.db` & `Raptor.Game.db` (Mob Spawn Timers)
- **`NpcDefs` table (524 NPC definitions in v0.13021.0):**
  - `DespawnedTime` (INTEGER, ms): Time an individual mob remains despawned after death before respawning (ranges from `200` ms to `223,000` ms; e.g. `Deer` = `3500` ms, `Weak Demon Brute` = `111000` ms).
  - `CorpseFadeTime` (INTEGER, ms): Time corpse stays visible before despawning.
- **`NpcGroupDefs` table (10 roaming/pack definitions):**
  - `RespawnTimeMs` (INTEGER, ms): Respawn timer for NPC packs/groups (e.g. `Thrunk` = `90000` ms, `Bandits` = `90000` ms, `KalFishers` = `60000` ms).
  - `RespawnTimeMaxMs` (INTEGER, ms): Optional upper bound for randomized pack respawn time.
- **Mob Spawn Timer Mod Patch:** Multiply `NpcDefs.DespawnedTime` and `NpcGroupDefs.RespawnTimeMs` (plus `RespawnTimeMaxMs` where `> 0`) by `MOB_RESPAWN_MULTIPLIER` (e.g. `0.5` for 2x faster respawns).

### E. Save File `gen-0001.db` (`CharacterFinances` table)
- **Columns:** `Id`, `CharacterId`, `Type`, `Value`
- **Regional Merits:** `Type` values 1 through 7 represent Merits earned in regions 1 through 7.

---

## 3. Exact Binary Offsets & PE Section Mappings (v0.13022.0)

> Every offset below belongs to **v0.13022.0 only**. The patchers verify the expected bytes before writing and refuse on any other version. To port to a new version, follow §4.

### A. `global-metadata.dat` (File size: 33,107,944 bytes, IL2CPP v31)
| Field / Concept | Offset (Hex) | Offset (Dec) | Original | Modded | Purpose |
|---|---|---|---|---|---|
| `max_craft_count` (field default value, field #13964) | `0x10af273` | `17,494,643` | `0x3c` (60) | `0xc8` (200) | Craft Many UI slider max limit (allows crafting up to 200 items in one batch). The 4 bytes after it (`96 00 00 00`) identify the spot. |

Resolved as: field name `max_craft_count` -> `fieldDefaultValues` entry -> `dataIndex` + `fieldAndParameterDefaultValueData` offset (`17,466,464`). It was at `0x10ad882` in v0.13021.0 and `0x105f1ca` in v0.13005.0.

### B. `GameAssembly.dll` (File size: 115,022,336 bytes)
- **PE Image Base:** `0x180000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400..0x47d800` (`foff = va - 0x180001000 + 0x400`)
  - `il2cpp`: RVA `0x47f000`, Raw `0x47d800..0x5295c00` (`foff = va - 0x18047f000 + 0x47d800`). **All the IL2CPP-compiled game methods live here.**
  - `.rdata`: RVA `0x5298000`, Raw `0x5295c00..0x61f9000`
  - `.data`: RVA `0x61fc000`, Raw `0x61f9000..0x68e5400` (`foff = va - 0x1861fc000 + 0x61f9000`)
- **`Il2CppCodeGenModule` (`InSpades.Client.dll`):**
  - Struct at file offset `0x5a05050`
  - `methodPointerCount`: `29,309`
  - `methodPointers` array: **File Offset `0x66f5d30`** (VA `0x1866f8d30` in `.data`)
  - Indexing formula by metadata token: `entry_foff = 0x66f5d30 + ((token & 0xFFFFFF) - 1) * 8`

| Method / Patch Target | Token | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|---|
| `EstateController.CalculateEstatePoints` | `0x6006789` | `0x2510590` | `0x182511d90` | `48 89 4c 24 08 53` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Player always has 100 available Estate Points. |
| `EstateController.CalculateMaxEstatePoints` | `0x600678a` | `0x2510d20` | `0x182512520` | `48 89 5c 24 08 57` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Max Estate Points capacity is 100. |
| `EstateController.IsPlotLockedByProgression` | `0x600678b` | `0x2511140` | `0x182512940` | `40 53 41 54 41 56 41 57 48 81` | `49 c7 00 00 00 00 00 31 c0 c3` | `mov qword ptr [r8], 0; xor eax, eax; ret` -> Plots are never locked by progression. |
| `TradingPanel.ShowBankBox` (`AllowWithdraw`, at function `+0x12a`) | `0x6002311` | `0x1c0e2ba` | `0x181c0faba` | `c6 83 00 01 00 00 00` | `c6 83 00 01 00 00 01` | `mov byte ptr [rbx + 0x100], 1` -> Sets `AllowWithdraw = true` for Bank Boxes (enables right-click/drag withdraw). |
| `TradingItemBox.HandleShiftClick` (Bank Box branch, at function `+0x55`) | `0x60022dd` | `0x1c673b5` | `0x181c68bb5` | `33 d2 48 8b cb e8 c1 00 00 00` | `eb 7f 90 90 90 90 90 90 90 90` | `jmp short +0x7f` -> Redirects the Bank Box click from `RefuseBankBoxWithdraw` to the `RequestWithdrawal` case (`+0xd6`). **Earlier versions of this map called this method `OnClick` with token `0x60020f1`; that was wrong, the patched method has always been `HandleShiftClick`.** |

Historical (v0.13005.0 only, no longer touched or restored): the old crafting-rarity hooks on `Formula.RollCraftQuality` and `CraftSession.Send` were removed because they broke crafting. The v0.13022.0 tooling no longer writes or "restores" those spots, because the old offsets would now land inside unrelated code.

### C. `Raptor.Game.exe` (Server Executable, NativeAOT x64, File size: 179,918,336 bytes)
- **PE Image Base:** `0x140000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400`, Size `0x4295600` (`foff = va - 0x140001000 + 0x400`)
  - `.rdata`: RVA `0x4297000`, Raw `0x4295a00`, Size `0x568dc00`
  - `.data`: RVA `0x9925000`, Raw `0x9923600`, Size `0x746a00`
  - `.pdata`: RVA `0xa288000`, Raw `0xa06a000`, Size `0x471c00` (12-byte `RUNTIME_FUNCTION` entries; gives exact function start and end)
- **Key Server Functions:**
  - `EstateManager.CanUpgradePlot`: VA `0x1417dc3a0` (was `0x1417cd9e0` in v0.13021.0). Calls `EstateProgression.TryCheckProgression` at `+0x4d4` and `EstateManager.CalculateEstatePoints` at `+0x4e5`.
  - `EstateManager.StartUpgradePreparation`: VA `0x1417dd7e0` (was `0x1417cee20` in v0.13021.0).
  - `MsgEstateHandler.Dispatch`: VA `0x1418b7560` (was `0x1418a5420`; the masked bytes match exactly).
  - `MsgItemHandler.Dispatch`: was VA `0x1419c7cc0` in v0.13021.0 and **changed again in v0.13022.0**: no function matches its signature (best candidate is only 8% identical, at `0x1419db6e0`, 6,985 bytes). It was not re-located, and the kit never patches it. **Bank Box server check, still not verified:** whether the server accepts Bank Box withdrawals needs an in-game test.

| Server Method / Patch Target | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|
| `EstateManager.CalculateEstatePoints` | `0x17df300` | `0x1417dff00` | `57 56 55 53 48 81` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Server always calculates 100 available Estate Points in `CanUpgradePlot`. |
| `EstateProgression.TryCheckProgression` | `0x17e1920` | `0x1417e2520` | `41 57 41 56 41 55 41 54 57 56 55 53 48 83 ec 38 48 8b f9 48 8b da 49 8b` (24B) | `31 c0 49 89 00 49 89 40 08 49 89 40 10 49 89 40 18 49 89 40 20 ff c0 c3` | Zeroes out `out LocalizedString lockedReason` (`[r8..r8+0x28]`) and returns `eax = 1` (`true`, not locked by progression). |
| `EstateManager.StartUpgradePreparation` (`ItemsForUpgrade` branch, at function `+0x135`) | `0x17dcd15` | `0x1417dd915` | `7f 16` | `90 90` | `nop; nop` -> Bypasses the `ItemsForUpgrade.Count > 0` check so the server always calls `StartUpgrade` for instant 0-material Estate room construction even if `Raptor.Game.db` was not modified. |
| `ItemManager.CalculateTransferAmount` (DO NOT PATCH) | not re-located | - | - | Vanilla | Authoritative ground item pickup & transfer capacity calculation used by `PickupAll` (Shift-F), `Withdraw`, and `Loot`. Must stay vanilla. The function changed in v0.13021.0 and was not searched for again in v0.13022.0, since the kit never patches it (it was `0x16b6f30` in v0.13005.0). |

---

## 4. Porting the offsets to a new game version

Offsets change on every update, so nothing here should be trusted blindly. The patchers enforce that: they read the bytes at each offset and stop if they are not the expected vanilla or patched bytes. To bring the kit forward:

1. **Do not run any patcher first.** Keep the freshly updated, untouched files. Old `.original_bak` files are from the previous version (and may even be modded), so they are not a usable baseline. The patchers refresh a backup whose size does not match the current file.
2. **Client methods (`GameAssembly.dll`), find them by name, not by address.** Parse `global-metadata.dat` (v31):
   - Header: after `magic` and `version`, each section is an `(offset, size)` pair of `uint32`, in this order: `stringLiteral`, `stringLiteralData`, `string`, `events`, `properties`, `methods`, ... `typeDefinitions` (20th pair), `images`, `assemblies`.
   - `typeDefinitions`: 88-byte records (16 `uint32`, 8 `uint16`, 2 `uint32`). `nameIndex` is field 0, `namespaceIndex` field 1, `methodStart` field 9, and the first `uint16` after the 16 `uint32` is `method_count`.
   - `methods`: 36-byte records (`nameIndex`, `declaringType`, `returnType`, `returnParameterToken`, `parameterStart`, `genericContainerIndex`, `token`, then 4 `uint16`). A method's `token & 0xFFFFFF` is its RID.
   - In `GameAssembly.dll`, find the string `InSpades.Client.dll\0`, then the 8-byte pointer to it. At that struct, `+8` is `methodPointerCount` and `+16` is the `methodPointers` array. The function VA is `methodPointers[RID - 1]`; convert it to a file offset with the section formulas above.
3. **Instructions inside a function** (`ShowBankBox`, `HandleShiftClick`): disassemble the old and new copies of the same method side by side (Capstone works well) and locate the same instruction. Field offsets and call targets drift; instruction shapes rarely do.
4. **Server functions (`Raptor.Game.exe`, NativeAOT):** there is no metadata. Use `.pdata` for exact function bounds, mask the RIP-relative `disp32` and `rel32` call/jmp operands of the old function, and search for that signature in the new binary. If a function changed, find it through a stable neighbour instead: `CanUpgradePlot` still calls `TryCheckProgression` and `CalculateEstatePoints` at the same relative spots.
5. **Metadata byte:** locate the `max_craft_count` field and read its `fieldDefaultValues` entry (see §3A).
6. **Databases:** with a pristine `Raptor.Game.db`, run `python gen_vanilla.py <path>` to rebuild the page's `VANILLA` table. It refuses a database that is already modded. Then run the page's logic on the real database as a round trip (strike everything, read the terms back, un-strike, and compare with the original).
7. Update the patch table in `everlast_stack_mod.py` and the matching table in `Everlast Mod Kit.html`, then test on **copies** of the game files before touching the real folder.

### What changed between v0.13005.0 and v0.13021.0
- Every method token shifted (about 2,200 new methods before the Estate and Trading code). All offsets above moved; the patched functions themselves are unchanged apart from field offsets.
- Crafting curse was removed from most recipes: 42 recipes in 13 component sets still carry `CurseGainOnCraft` (it was 657 recipes in 69 sets). Gathering (12 sets) and stealing (2 sets) curses are unchanged.
- Potato, Sweetberry, Mushroom and Apple stack to 10 (was 5). The Bucket is now stackable to 5. Potions are now `Stackable = 1, MaxStackSize = 1` instead of `Stackable = 0`.
- `ItemDefs` gained a `ReplacedBy` column and new items (ids up to 1234). `NpcDefs` has 524 rows (was 513). `AbilityDefs` gained one curse-bearing ability (id 306).

### What changed between v0.13021.0 and v0.13022.0
- A small update: about 40 new client methods (`methodPointerCount` 29,269 to 29,309), so every metadata token after the Estate and Trading code moved by a few and every file offset shifted (the server code moved by about `0xe9c0` bytes).
- All 9 patched functions are byte-for-byte identical apart from relative call and RIP-relative displacements. Each one was re-found by name (client, through the metadata tokens) or by masked signature (server, through `.pdata`), and the server matches scored 100%.
- The `VANILLA` table rebuilt from the fresh `Raptor.Game.db` came out identical to the v0.13021.0 one, so no database values the kit touches changed.
