# Everlast Mod: Crafting Rarity & Binary Handoff Document for Claude

**Date:** November 4, 2026  
**Target Game:** Everlast (Steam release, 64-bit Windows)  
**Install Path:** `D:\SteamLibrary\steamapps\common\Everlast`  
**Mod Kit Repo:** `c:\Projects\GameMods\Everlast`  
**Master Internals Map:** `c:\Projects\GameMods\Everlast\EVERLAST_INTERNALS_MAP.md`  

> **RESOLVED 2026-11-04 (Claude):** Crafting restored. Both client crafting patches (`0x1e8041b`, `0x35d7230`) were reverted to vanilla in the installed `GameAssembly.dll`, and the rarity feature was removed from the Mod Kit. Its patcher now always restores those bytes. Crafting rarity is shelved: quality is rolled inside `Raptor.Game.exe` with no data-driven weights in any `.db`. Some VA/file-offset pairs below are inconsistent; verify before using.

---

## 1. Executive Summary & Immediate Unblock

### Current Status
Crafting is currently failing/refusing to start in the user's game because of a hooked packet field at `GameAssembly.dll:0x1e8041b`. 

### The Root Cause Discovered
1. We initially assumed offset `+0x48` in the craft message struct was the **Item Quality Rank** (`ItemQuality`: 0 = Common, 1 = Uncommon, 2 = Rare, 3 = Epic, 4 = Legendary / Masterwork).
2. **Reverse engineering of `global-metadata.dat` revealed that field `+0x48` is actually `MsgCraft.MaterialMultiplier`** (the 1x / 2x / 3x / 4x ingredient overcharge multiplier).
3. Writing `4` into `[rdx + 0x48]` told the server that the player was submitting **4x the required materials**.
4. If the player only has 1x materials in their bags, or if the recipe doesn't support extra materials, the server rejects the craft packet with `"Can't craft - Extra materials can't raise this craft above S"` or silently refuses to start because the player lacks the 4x materials!

### Instant Reversion (How to Unblock the User Right Now)
To immediately restore vanilla crafting without touching working patches (Estate Points, Bank Boxes, Craft Many 200), restore the 13 vanilla bytes at `GameAssembly.dll:0x1e8041b`:
```powershell
$dll = 'D:\SteamLibrary\steamapps\common\Everlast\GameAssembly.dll'
$fs = [IO.File]::Open($dll, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
[void]$fs.Seek(0x1e8041b, 0)
# Vanilla 13 bytes: cmp esi, 1; ja +4; mov r10d, [rbx+0x74]; mov [rdx+0x48], r10d
$fs.Write([byte[]]@(0x83, 0xfe, 0x01, 0x77, 0x04, 0x44, 0x8b, 0x53, 0x74, 0x44, 0x89, 0x52, 0x48), 0, 13)
$fs.Close()
Write-Host "Vanilla crafting restored successfully!" -ForegroundColor Green
```
Full original backups also exist at:
- `D:\SteamLibrary\steamapps\common\Everlast\GameAssembly.dll.original_bak`
- `D:\SteamLibrary\steamapps\common\Everlast\Everlast_Data\StreamingAssets\Server\Windows\Raptor.Game.exe.original_bak`

---

## 2. Architecture & Tech Stack

Everlast uses a **client-server local architecture**:
- **Client:** Unity IL2CPP 64-bit (`GameAssembly.dll`). Image base: `0x180000000`. Handles UI, rendering, client input, and sends network packets to the local server.
- **Server:** .NET NativeAOT 64-bit (`Everlast_Data\StreamingAssets\Server\Windows\Raptor.Game.exe`). Image base: `0x140000000`. Runs locally on loopback. Authoritative for all inventory, item generation, crafting validation, and database writes.
- **Metadata:** `Everlast_Data\il2cpp_data\Metadata\global-metadata.dat` (IL2CPP v31).
- **Databases:** SQLite save files located at:
  `C:\Users\<user>\Documents\My Games\Everlast\Worlds\<WorldName>\save\gen-0001.db`

---

## 3. Working Patches in the Mod Kit (DO NOT BREAK)

These features are completely tested, verified, and functional:
1. **Estate Points 100 Capacity & Progression Unlock:**
   - Client (`GameAssembly.dll`):
     - `EstateController.CalculateEstatePoints` (Token `0x6005ea3`, FileOff `0x23a2230`): `b8 64 00 00 00 c3` (`mov eax, 100; ret`)
     - `EstateController.CalculateMaxEstatePoints` (Token `0x6005ea4`, FileOff `0x23a29c0`): `b8 64 00 00 00 c3` (`mov eax, 100; ret`)
     - `EstateController.IsPlotLockedByProgression` (Token `0x6005ea5`, FileOff `0x23a2de0`): `49 c7 00 00 00 00 00 31 c0 c3` (`mov [r8], 0; xor eax, eax; ret`)
   - Server (`Raptor.Game.exe`):
     - `EstateManager.CalculateEstatePoints` (FileOff `0x173cc40`): `b8 64 00 00 00 c3`
     - `EstateProgression.TryCheckProgression` (FileOff `0x173f260`): `31 c0 49 89 00 49 89 40 08 49 89 40 10 49 89 40 18 49 89 40 20 ff c0 c3`
2. **Craft Many Slider Limit (60 -> 200):**
   - File: `Everlast_Data\il2cpp_data\Metadata\global-metadata.dat`
   - File offset: `0x105f1ca`
   - Vanilla: `0x3c` (60) -> Patched: `0xc8` (200)
3. **Bank Box Withdrawals (Enable Drag/Right-Click & Click):**
   - Client (`GameAssembly.dll`):
     - `TradingPanel.ShowBankBox` (`AllowWithdraw` flag, FileOff `0x1bda84e`): `c6 83 00 01 00 00 01` (`mov byte [rbx+0x100], 1`)
     - `TradingItemBox.OnClick` (`BankBox` branch, FileOff `0x1bd1cf5`): `eb 7f 90 90 90 90 90 90 90 90` (`jmp short 0x181bd3376` -> bypasses `RefuseBankBoxWithdraw`)
4. **Shift-F Bulk Pickup Protection:**
   - Target: `ItemManager.CalculateTransferAmount` in `Raptor.Game.exe` at file offset `0x16b6f30`.
   - **CRITICAL CONSTRAINT:** MUST REMAIN 100% VANILLA. Patching this breaks bulk ground pickup and inventory stacking.

---

## 4. The Crafting Quality / Rarity Problem

### The Goal
The user wants crafted items to come out as **Tier 4 (Masterwork / Legendary / Orange)**, or have customizable percentage chances for:
- Tier 4: Masterwork / Legendary (Orange)
- Tier 3: Flawless / Epic (Purple)
- Tier 2: Superior / Rare (Blue)
- Tier 1: Fine / Uncommon (Green)
- Tier 0: Normal / Common (White/Gray)

### What the Client Sends (`MsgCraft`)
From `global-metadata.dat` analysis of class `InSpades.Client.CraftingPanel.StartCraft` (Token `0x600357b`, VA `0x181e7fc00`, FileOff `0x1e7fc00`):
- `esi` holds `craftType`:
  - `0`: Standard manual craft
  - `1`: Auto / Bulk craft
  - `2`: Focused Craft (interactive minigame)
- The method prepares `MsgCraft` struct (`rdx`):
  - `+0x00`: Packet header
  - `+0x18`: ObjectUId
  - `+0x20`: CraftType
  - `+0x28`: ItemIds
  - `+0x38`: CrafterSetName
  - `+0x40`: CrafterName
  - `+0x48`: `MaterialMultiplier` (int32)
- Vanilla code at `GameAssembly.dll:0x1e8041b`:
  ```x86asm
  83 fe 01                cmp esi, 1
  77 04                   ja  skip_multiplier
  44 8b 53 74             mov r10d, dword ptr [rbx + 0x74]  ; rbx+0x74 = this.MaterialMultiplier
  skip_multiplier:
  44 89 52 48             mov dword ptr [rdx + 0x48], r10d  ; packet->MaterialMultiplier
  ```
  *Notice: When `esi > 1` (Focused Craft), `r10d` was initialized to 0 earlier (`xor r10d, r10d` at `0x1e8021f`), so `MaterialMultiplier = 0`.*

### Where Quality Actually Lives: Server Authoritative
Because `MsgCraft` has no quality field, the **server (`Raptor.Game.exe`) rolls the item quality authoritatively**.

In `Raptor.Game.exe`:
1. Craft message processing function:
   - RVA: `0x190f060..0x1910dd1`
   - VA: `0x14190f060`
   - File Offset: `0x190e460` (Length: 7,537 bytes)
2. Relevant string literals in `Raptor.Game.exe`:
   - `0x9725718` (VA `0x149727118`): `"Can't craft - Extra materials can't raise this craft above S."`
   - `0x97257a8` (VA `0x1497271a8`): `"Can't craft - Focused crafts use normal materials."`
3. Method names in reflection metadata at `0x483a000`:
   - `WeightedRandomSelectIndex`
   - `RollFromWeights`
   - `GetQualityPriceMultiplier`
   - `GetCraftQualityWeights`
   - `RollCraftQuality`
   - `RollItemQuality`
4. Client counterpart in `GameAssembly.dll`:
   - `Formula.GetCraftQualityWeights` (File offset `0x35d70b8`, VA `0x1835d70b8`)
   - `Formula.RollCraftQuality` (File offset `0x35d7230`, VA `0x1835d8830`)
   - In vanilla, `GetCraftQualityWeights` loads from static arrays:
     - `AutoCraftQualityWeights` (at static fields `+0x10`)
     - `FocusedCraftQualityWeights` (at static fields `+0x18`)
     - These weight arrays are passed to `RollFromWeights` / `WeightedRandomSelectIndex` to return `0..4`.

---

## 5. Potential Attack Vectors for Claude

### Vector A: Server Binary Patch in `Raptor.Game.exe` (Cleanest & Most Direct)
Find `Formula.RollCraftQuality` or `Formula.RollFromWeights` in `Raptor.Game.exe`:
- Look at calls made from `ProcessCraft` (`0x14190f060` / FileOff `0x190e460`).
- Target candidates discovered in the call analysis of `ProcessCraft`:
  - `0x141801fc0` (FileOff `0x18013c0`)
  - `0x141802020` (FileOff `0x1802020`)
  - `0x141802230` (FileOff `0x1801630`)
- Patching the server's `RollCraftQuality` or `WeightedRandomSelectIndex` to return `4` (or uniform Lemire reduction against custom percentage thresholds) guarantees 100% server-authoritative Masterwork items without touching client packets.

### Vector B: Static Weight Array Patching
`AutoCraftQualityWeights` is an array of integer weights for tiers `[Common, Uncommon, Rare, Epic, Legendary]`.
- In vanilla, standard crafting has weights like `[80, 15, 5, 0, 0]`.
- If the static array in `Formula..cctor` is patched (e.g. `[0, 0, 0, 0, 100]`), all auto-crafts naturally resolve to Tier 4 without modifying control flow.

### Vector C: Item / Recipe SQLite Database Tables
Check `C:\Users\<user>\Documents\My Games\Everlast\Worlds\<WorldName>\save\gen-0001.db` (or game data databases) for:
- `recipes` table: Can recipes have an explicit base quality or guarantee high-tier rolls?
- `terms` table: Are crafting outcome multipliers defined as database terms?

---

## 6. Project Files Map

- **Master Internals Reference:** [`c:\Projects\GameMods\Everlast\EVERLAST_INTERNALS_MAP.md`](file:///c:/Projects/GameMods/Everlast/EVERLAST_INTERNALS_MAP.md) — Contains full DB schema, exact IL2CPP token map, PE section tables.
- **Python Mod Engine:** [`c:\Projects\GameMods\Everlast\everlast_stack_mod.py`](file:///c:/Projects/GameMods/Everlast/everlast_stack_mod.py) — Standalone automation script.
- **Web Mod Kit & GUI:** [`c:\Projects\GameMods\Everlast\Everlast Mod Kit.html`](file:///c:/Projects/GameMods/Everlast/Everlast%20Mod%20Kit.html) — 3-tab browser GUI (Contract, Executables Patcher, World Rider).
- **Steam Guide Text:** [`c:\Projects\GameMods\Everlast\steam-guide.txt`](file:///c:/Projects/GameMods/Everlast/steam-guide.txt)
- **Repo README:** [`c:\Projects\GameMods\Everlast\README.md`](file:///c:/Projects/GameMods/Everlast/README.md)

