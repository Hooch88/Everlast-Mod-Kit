# Everlast Internal Architecture & Modification Knowledge Map

> **Purpose:** Comprehensive, persistent reference mapping all files, database tables, schemas, IL2CPP structures, and exact binary patch offsets for Everlast. Eliminates the need for repetitive scans.
> **Game Directory:** `D:\SteamLibrary\steamapps\common\Everlast`
> **User Saves Directory:** `%LOCALAPPDATA%\InSpades\Everlast\Worlds\<WorldName> (Legacy: %USERPROFILE%\Documents\My Games\Everlast\Worlds\<WorldName>)`
> **Mod Kit Project:** `C:\Projects\GameMods\Everlast`
> **Verified against:** Everlast v0.13021.0 (Steam build 26648859). Byte offsets in section 3 are for this version only; see section 4 to port them after a game update.

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

## 3. Exact Binary Offsets & PE Section Mappings (v0.13021.0)

> Every offset below belongs to **v0.13021.0 only**. The patchers verify the expected bytes before writing and refuse on any other version. To port to a new version, follow §4.

### A. `global-metadata.dat` (File size: 33,098,352 bytes, IL2CPP v31)
| Field / Concept | Offset (Hex) | Offset (Dec) | Original | Modded | Purpose |
|---|---|---|---|---|---|
| `max_craft_count` (field default value, field #13954) | `0x10ad882` | `17,488,002` | `0x3c` (60) | `0xc8` (200) | Craft Many UI slider max limit (allows crafting up to 200 items in one batch). The 4 bytes after it (`96 00 00 00`) identify the spot. |

Resolved as: field name `max_craft_count` -> `fieldDefaultValues` entry -> `dataIndex` + `fieldAndParameterDefaultValueData` offset (`17,459,824`). In v0.13005.0 this byte was at `0x105f1ca`.

### B. `GameAssembly.dll` (File size: 114,973,184 bytes)
- **PE Image Base:** `0x180000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400..0x47d600` (`foff = va - 0x180001000 + 0x400`)
  - `il2cpp`: RVA `0x47f000`, Raw `0x47d600..0x528be00` (`foff = va - 0x18047f000 + 0x47d600`). **All the IL2CPP-compiled game methods live here.**
  - `.rdata`: RVA `0x528e000`, Raw `0x528be00..0x61ede00`
  - `.data`: RVA `0x61f0000`, Raw `0x61ede00..0x68d9a00` (`foff = va - 0x1861f0000 + 0x61ede00`)
- **`Il2CppCodeGenModule` (`InSpades.Client.dll`):**
  - Struct at file offset `0x59facc0` (the module name string is at `0x59d97f0`)
  - `methodPointerCount`: `29,269`
  - `methodPointers` array: **File Offset `0x66ea6b0`** (VA `0x1866ec8b0` in `.data`)
  - Indexing formula by metadata token: `entry_foff = 0x66ea6b0 + ((token & 0xFFFFFF) - 1) * 8`

| Method / Patch Target | Token | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|---|
| `EstateController.CalculateEstatePoints` | `0x6006761` | `0x2509310` | `0x18250ad10` | `48 89 4c 24 08 53` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Player always has 100 available Estate Points. |
| `EstateController.CalculateMaxEstatePoints` | `0x6006762` | `0x2509aa0` | `0x18250b4a0` | `48 89 5c 24 08 57` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Max Estate Points capacity is 100. |
| `EstateController.IsPlotLockedByProgression` | `0x6006763` | `0x2509ec0` | `0x18250b8c0` | `40 53 41 54 41 56 41 57 48 81` | `49 c7 00 00 00 00 00 31 c0 c3` | `mov qword ptr [r8], 0; xor eax, eax; ret` -> Plots are never locked by progression. |
| `TradingPanel.ShowBankBox` (`AllowWithdraw`, at function `+0x12a`) | `0x6002309` | `0x1c0c41a` | `0x181c0de1a` | `c6 83 00 01 00 00 00` | `c6 83 00 01 00 00 01` | `mov byte ptr [rbx + 0x100], 1` -> Sets `AllowWithdraw = true` for Bank Boxes (enables right-click/drag withdraw). |
| `TradingItemBox.HandleShiftClick` (Bank Box branch, at function `+0x55`) | `0x60022d5` | `0x1c64355` | `0x181c65d55` | `33 d2 48 8b cb e8 c1 00 00 00` | `eb 7f 90 90 90 90 90 90 90 90` | `jmp short +0x7f` -> Redirects the Bank Box click from `RefuseBankBoxWithdraw` to the `RequestWithdrawal` case (`+0xd6`). **Earlier versions of this map called this method `OnClick` with token `0x60020f1`; that was wrong, the patched method has always been `HandleShiftClick`.** |

Historical (v0.13005.0 only, no longer touched or restored): the old crafting-rarity hooks on `Formula.RollCraftQuality` and `CraftSession.Send` were removed because they broke crafting. The v0.13021.0 tooling no longer writes or "restores" those spots, because the old offsets would now land inside unrelated code.

### C. `Raptor.Game.exe` (Server Executable, NativeAOT x64, File size: 179,701,760 bytes)
- **PE Image Base:** `0x140000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400`, Size `0x4275a00` (`foff = va - 0x140001000 + 0x400`)
  - `.rdata`: RVA `0x4277000`, Raw `0x4275e00`, Size `0x567fa00`
  - `.data`: RVA `0x98f7000`, Raw `0x98f5800`, Size `0x742000`
  - `.pdata`: RVA `0xa255000`, Raw `0xa037800`, Size `0x470000` (12-byte `RUNTIME_FUNCTION` entries; gives exact function start and end)
- **Key Server Functions:**
  - `EstateManager.CanUpgradePlot`: VA `0x1417cd9e0` (was `0x141739ce0`). Calls `EstateProgression.TryCheckProgression` at `+0x4d4` and `EstateManager.CalculateEstatePoints` at `+0x4e5`.
  - `EstateManager.StartUpgradePreparation`: VA `0x1417cee20` (was `0x14173b120`).
  - `EstateManager` entry used by `MsgEstateHandler.Dispatch`: VA `0x1417ccec0`. `MsgEstateHandler.Dispatch`: VA `0x1418a5420` (best match, 866 of 871 fixed bytes).
  - `MsgItemHandler.Dispatch`: VA `0x1419c7cc0` (was `0x1418ee320`). The `Deposit` call is at `+0x45f`. **Bank Box server check, not verified:** the Withdraw and Deposit cases are still structurally parallel, but the function gained extra reads of two message fields (`[r8 + 0x20]`, `[r8 + 0x2c]`) and a changed enum compare (`cmp r9d, 0x23` became `0x2a`). Whether the server still accepts Bank Box withdrawals needs an in-game test.

| Server Method / Patch Target | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|
| `EstateManager.CalculateEstatePoints` | `0x17d0940` | `0x1417d1540` | `57 56 55 53 48 81` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Server always calculates 100 available Estate Points in `CanUpgradePlot`. |
| `EstateProgression.TryCheckProgression` | `0x17d2f60` | `0x1417d3b60` | `41 57 41 56 41 55 41 54 57 56 55 53 48 83 ec 38 48 8b f9 48 8b da 49 8b` (24B) | `31 c0 49 89 00 49 89 40 08 49 89 40 10 49 89 40 18 49 89 40 20 ff c0 c3` | Zeroes out `out LocalizedString lockedReason` (`[r8..r8+0x28]`) and returns `eax = 1` (`true`, not locked by progression). |
| `EstateManager.StartUpgradePreparation` (`ItemsForUpgrade` branch, at function `+0x135`) | `0x17ce355` | `0x1417cef55` | `7f 16` | `90 90` | `nop; nop` -> Bypasses the `ItemsForUpgrade.Count > 0` check so the server always calls `StartUpgrade` for instant 0-material Estate room construction even if `Raptor.Game.db` was not modified. |
| `ItemManager.CalculateTransferAmount` (DO NOT PATCH) | not re-located | - | - | Vanilla | Authoritative ground item pickup & transfer capacity calculation used by `PickupAll` (Shift-F), `Withdraw`, and `Loot`. Must stay vanilla. The function changed in v0.13021.0 and was not searched for again, since the kit never patches it (it was `0x16b6f30` in v0.13005.0). |

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
