# Everlast Internal Architecture & Modification Knowledge Map

> **Purpose:** Comprehensive, persistent reference mapping all files, database tables, schemas, IL2CPP structures, and exact binary patch offsets for Everlast. Eliminates the need for repetitive scans.
> **Game Directory:** `D:\SteamLibrary\steamapps\common\Everlast`
> **User Saves Directory:** `%USERPROFILE%\OneDrive\Documents\My Games\Everlast\Worlds\<WorldName>`
> **Mod Kit Project:** `C:\Projects\GameMods\Everlast`

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
| `%USERPROFILE%\OneDrive\Documents\My Games\Everlast\Worlds\<World>\save\gen-0001.db` | SQLite | Player world save database (inventory, finances/merits, character skills). |

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
  - **Id = 1130, 1131, 1132, 1133 (Altar & Shrine Exp):**
    - Contains: `ShrineProcessorComponent` / Sacrifice & Purify EXP granting rewards.
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
- **`NpcDefs` table (509 NPC definitions):**
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

## 3. Exact Binary Offsets & PE Section Mappings

### A. `global-metadata.dat` (File size: ~20.9 MB)
| Field / Concept | Offset (Hex) | Offset (Dec) | Original | Modded | Purpose |
|---|---|---|---|---|---|
| `max_craft_count` | `0x105f1ca` | `17,166,794` | `0x3c` (60) | `0xc8` (200) | Craft Many UI slider max limit (allows crafting up to 200 items in one batch). |
| String Literal `Estate Points` | Literal #13377 | `836,081` | - | - | String: `Estate Points: {points} / {max}` |
| `ZoneMeritsPerEstatePoint` | Field #56732 | `17,574,415` | Default | - | Constant in `Raptor.Database.Domain.Game.Data.Constants`. |

### B. `GameAssembly.dll` (File size: 112,921,088 bytes)
- **PE Image Base:** `0x180000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400..0x473a00` (`foff = va - 0x180001000 + 0x400`)
  - `il2cpp`: RVA `0x475000`, Raw `0x473a00..0x50f9200` (`foff = va - 0x180475000 + 0x473a00`)
  - `.rdata`: RVA `0x50fb000`, Raw `0x50f9200..0x6022a00` (`foff = va - 0x1850fb000 + 0x50f9200`)
  - `.data`: RVA `0x6025000`, Raw `0x6022a00..0x66f7200` (`foff = va - 0x186025000 + 0x6022a00`)
- **`Il2CppCodeGenModule` (`InSpades.Client.dll`):**
  - Struct at file offset `0x5831240` (VA `0x185833040`)
  - `methodPointerCount`: `26,889` (`0x6909`)
  - `methodPointers` array: **File Offset `0x650f380`** (VA `0x186511980` in `.data`)
  - Indexing formula by metadata token: `entry_foff = 0x650f380 + ((token & 0xFFFFFF) - 1) * 8`

| Method / Patch Target | Token / RID | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|---|
| `EstateController.CalculateEstatePoints` | `0x6005ea3` (24226) | `0x23a2230` | `0x1823a3830` | `48 89 5c 24 10 48` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Player always has 100 available Estate Points. |
| `EstateController.CalculateMaxEstatePoints` | `0x6005ea4` (24227) | `0x23a29c0` | `0x1823a3fc0` | `48 89 5c 24 08 48` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Max Estate Points capacity is 100. |
| `EstateController.IsPlotLockedByProgression` | `0x6005ea5` (24228) | `0x23a2de0` | `0x1823a43e0` | `48 89 5c 24 08 48` | `49 c7 00 00 00 00 00 31 c0 c3` | `mov qword ptr [r8], 0; xor eax, eax; ret` -> Plots are never locked by progression. |
| `Formula.RollCraftQuality` (Client UI Roll) | `0x6000028` (40) | `0x35d7230` | `0x1835d8830` | `48 89 5c 24 08 57` | Custom 64B RNG | Injects fast Lemire reduction (`rdtsc + imul + mul 100`) against customizable percentage thresholds for tiers 0..4 (Normal..Masterwork). |
| `TradingPanel.ShowBankBox` (`AllowWithdraw`) | `0x6002128` | `0x1bda84e` | `0x181bdbe4e` | `c6 83 00 01 00 00 00` | `c6 83 00 01 00 00 01` | `mov byte ptr [rbx + 0x100], 1` -> Sets `AllowWithdraw = true` for Bank Boxes (enables right-click/drag withdraw). |
| `TradingItemBox.OnClick` (`BankBox` branch) | `0x60020f1` | `0x1bd1cf5` | `0x181bd32f5` | `33 d2 48 8b cb e8 c1 00 00 00` | `eb 7f 90 90 90 90 90 90 90 90` | `jmp short 0x181bd3376` -> Redirects Bank Box left-click from `RefuseBankBoxWithdraw` to `RequestWithdrawal`. |

### C. `Raptor.Game.exe` (Server Executable, NativeAOT x64)
- **PE Image Base:** `0x140000000`
- **PE Sections:**
  - `.text`: RVA `0x1000`, Raw `0x400`, Size `0x4115800` (`foff = va - 0x140001000 + 0x400`)
  - `.rdata`: RVA `0x4117000`, Raw `0x4115c00`, Size `0x5558a00`
  - `.data`: RVA `0x9670000`, Raw `0x966e600`, Size `0x718600`
  - `.pdata`: RVA `0x9f9c000`, Raw `0x9d86c00`, Size `0x45fa00` (382,151 12-byte function boundary entries)
- **Key Server Functions & Patches:**
  - `MsgItemHandler.Dispatch`: VA `0x1418ee320` (FileOff `0x18ed720`)
    - `Withdraw` case: VA `0x1418ee585` (FileOff `0x18ed985`) -> calls `0x1417f0ce0`, `0x14169a410`, and `ItemManager.Withdraw` (`0x1417589a0`).
    - `Deposit` case: VA `0x1418ee702` (FileOff `0x18edb02`) -> calls the exact same `0x1417f0ce0` and `0x14169a410` checks, then `ItemManager.Deposit` (`0x141756080`). Because the server checks are identical for Deposit and Withdraw, client-side Bank Box withdrawal patches work without needing a server binary patch.
  - `MsgEstateHandler.Dispatch`: VA `0x1417ecd80` (FileOff `0x17ec180`) -> dispatches estate upgrade requests to `EstateManager` (`0x1417391c0` -> `StartUpgradePreparation` at `0x14173b120` -> `CanUpgradePlot` at `0x141739ce0`).

| Server Method / Patch Target | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|
| `EstateManager.CalculateEstatePoints` | `0x173cc40` | `0x14173d840` | `57 56 55 53 48 81` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Server always calculates 100 available Estate Points in `CanUpgradePlot` (`0x14173a1c5`). |
| `EstateProgression.TryCheckProgression` | `0x173f260` | `0x14173fe60` | `41 57 41 56 41 55 ...` (24B) | `31 c0 49 89 00 49 89 40 08 49 89 40 10 49 89 40 18 49 89 40 20 ff c0 c3` | Zeroes out `out LocalizedString lockedReason` (`[r8..r8+0x20]`) and returns `eax = 1` (`true`, not locked by progression). |
| `Formula.RollCraftQuality` (Server Authoritative) | `0x16b6f30` | `0x1416b7b30` | `55 41 56 57 56 53` | Custom 64B RNG | Injects fast Lemire reduction (`rdtsc + imul + mul 100`) against customizable percentage thresholds for tiers 0..4 (Normal..Masterwork). Generates authoritative quality and modifiers in `CreateItemWithQuality`. |
