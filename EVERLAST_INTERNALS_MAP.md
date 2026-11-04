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
| `Assets\Database\Definitions\ComponentSetDefs.db` | SQLite | Definitions of event/game components (Desolate zones, Altar/Shrine xp rewards). |
| `Assets\Database\Definitions\EstatePlotDefs.db` | SQLite | Definitions of estate plots, labels, upgrade requirements (`ItemsForUpgrade`). |
| `Everlast_Data\StreamingAssets\Server\Windows\Raptor.Data\Raptor.Game.db` | SQLite | Server-side replica of definitions (must stay in sync with client `.db` files). |
| `Everlast_Data\StreamingAssets\Server\Windows\Raptor.Game.exe` | PE AOT .NET | Dedicated server executable (hosts local/MP session; handles game logic). |
| `Everlast_Data\il2cpp_data\Metadata\global-metadata.dat` | IL2CPP v31 | Client type definitions, string literals, fields, method metadata. |
| `GameAssembly.dll` | PE x64 Native | Compiled IL2CPP native client code for all client assemblies. |
| `%USERPROFILE%\OneDrive\Documents\My Games\Everlast\Worlds\<World>\save\gen-0001.db` | SQLite | Player world save database (inventory, finances/merits, character skills). |

---

## 2. Database Tables & Mod Schemas

### A. `ItemDefs.db` & `Raptor.Game.db` (`ItemDefs` table)
- **Primary Key:** `Id` (INTEGER)
- **Key Columns:**
  - `StackSize` (INTEGER): Default is 1, 10, 20, 50, 100 depending on item category.
  - `Name` (TEXT): Display name token or text.
  - `Category` (INTEGER): Item category index.
  - `Tags` (TEXT / JSON array): E.g. `["Consumable", "Food"]`, `["Currency"]`, `["Curse"]`.
- **Mod Patch:** Stacking mod updates `StackSize = 100` (or configured value) where stackable items are grouped.

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

### C. `EstatePlotDefs.db` & `Raptor.Game.db` (`EstatePlotDefs` table)
- **Primary Key:** `Id` (INTEGER)
- **Key Column:** `Variants` (TEXT JSON Array)
  - Each variant object contains:
    - `VariantId` (INTEGER): 1, 2, 3...
    - `Label` (TEXT): Display name of building/upgrade.
    - `SelectableForUpgrade` (BOOLEAN): `true` if player can choose it.
    - `ItemsForUpgrade` (ARRAY): List of required item IDs and amounts, e.g. `[{"ItemId": 45, "Amount": 100}]`.
- **Free Estate Build Mod Patch:** Set `ItemsForUpgrade = []` across all variants.

### D. Save File `gen-0001.db` (`CharacterFinances` table)
- **Columns:** `Id`, `CharacterId`, `Type`, `Value`
- **Regional Merits:** `Type` values 1 through 7 represent Merits earned in regions 1 through 7.
- **Rule:** In vanilla, every region's merits only yield 1 Estate Point (total 5-7 points max), meaning full estate buildout is blocked without client patching.

---

## 3. Exact Binary Offsets & IL2CPP Patches

### A. `global-metadata.dat` (File size: ~20.9 MB)
| Field / Concept | Offset (Hex) | Offset (Dec) | Original | Modded | Purpose |
|---|---|---|---|---|---|
| `max_craft_count` | `0x105f1ca` | `17,166,794` | `0x3c` (60) | `0xc8` (200) | Craft Many UI slider max limit (allows crafting up to 200 items in one batch). |
| String Literal `Estate Points` | Literal #13377 | `836,081` | - | - | String: `Estate Points: {points} / {max}` |
| `ZoneMeritsPerEstatePoint` | Field #56732 | `17,574,415` | Default | - | Constant in `Raptor.Database.Domain.Game.Data.Constants`. |

### B. `GameAssembly.dll` (File size: ~112.9 MB)
- **PE Image Base:** `0x180000000`
- **Method Pointer Table (`InSpades.Client.dll`):** File offset `0x556a268` (VA `0x18556c068`), 24,233 entries.

| Method Name | Method ID | File Offset | Virtual Address | Original Bytes | Patched Bytes | Patch Purpose |
|---|---|---|---|---|---|---|
| `EstateController.CalculateEstatePoints` | 24226 | `0xe929f0` | `0x180e93ff0` | `48 89 5c 24 08 48` | `b8 64 00 00 00 c3` | `mov eax, 100; ret` -> Player always has 100 available Estate Points. |
| `EstateController.CalculateMaxEstatePoints` | 24227 | Table `0x5599780` | `0x18559b580` | `a0 40 e9 80 01 00 00 00` | `f0 3f e9 80 01 00 00 00` | Points to `0x180e93ff0` -> Max capacity displays 100 points. |
| `EstateController.IsPlotLockedByProgression` | 24228 | `0xe92aa0` | `0x180e940a0` | `48 89 54 24 10 48` | `31 c0 c3 90 90 90` | `xor eax, eax; ret` -> Plots are never locked by progression blocks. |

---

## 4. Summary of Mod Patches Needed for Complete Estate & Crafting Freedom

1. **Craft Many = 200:**
   - Patch `global-metadata.dat` offset `17166794` from `0x3c` to `0xc8`.
2. **Free Estate Construction (Materials):**
   - Set `ItemsForUpgrade = []` for all plot variants in `EstatePlotDefs.db` and `Raptor.Game.db`.
3. **Free Estate Points & Progression Unlock:**
   - Patch `GameAssembly.dll` at `0xe929f0` to return `100` (`b8 64 00 00 00 c3`).
   - Patch `GameAssembly.dll` pointer table at `0x5599780` to point to `0x180e93ff0` (`f0 3f`).
   - Patch `GameAssembly.dll` at `0xe92aa0` to return `false` (`31 c0 c3 90 90 90`).

