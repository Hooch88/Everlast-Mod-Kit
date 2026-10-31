import sqlite3
import re
import os
import shutil

EVERLAST_DIR = r"D:\SteamLibrary\steamapps\common\Everlast"
BACKUP_DIR = os.path.join(EVERLAST_DIR, "ModBackups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# CONFIGURATION OPTIONS:
# 1. Stacking:
ENABLE_STACKING = True
NEW_STACK_SIZE = 100        # Empty Buckets, Potions, Cooked Food/Pies, Moulds, Hand Tools, Unstrung Bows
RESOURCE_STACK_SIZE = 100   # Milk, Water, Ores, Bars, Logs, Raw Fish, Herbs, Gems, Leathers

# 2. Curse Removal:
REMOVE_GATHERING_CURSE = True   # Mining ores, chopping trees, gathering herbs, fishing
REMOVE_COMBAT_CURSE = True      # Weapon attacks, basic swings, spells, dodging
REMOVE_STEALING_CURSE = True    # Stealing world items / pumpkins / beer

# 3. Totem Multiplier (Optional buff to cleansing items if player wants):
TOTEM_CLEANSE_MULTIPLIER = 1.0  # 1.0 = vanilla (-15/-30/-45/-60), 2.0 = double strength

TOTEM_BASES = {
    'Fragile Totem': -15,
    'Stable Totem': -30,
    'Robust Totem': -45,
    'Mighty Totem': -60
}

def apply_stack_mod():
    db_paths = [
        os.path.join(EVERLAST_DIR, r"Assets\Database\Definitions\ItemDefs.db"),
        os.path.join(EVERLAST_DIR, r"Everlast_Data\StreamingAssets\Server\Windows\Raptor.Data\Raptor.Game.db")
    ]
    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 1. Upgrade existing resource items (ores, bars, logs, milk, water, etc.) to RESOURCE_STACK_SIZE
        cur.execute("""
            UPDATE ItemDefs
            SET MaxStackSize = ?
            WHERE Stackable = 1 AND MaxStackSize IN (5, 20, 40, ?)
        """, (RESOURCE_STACK_SIZE, RESOURCE_STACK_SIZE))

        # 2. Make non-stackables (Potions, Food, Moulds, Hand Tools, Unstrung Bows) stack to NEW_STACK_SIZE
        # In build 1389+, PouchStackSize is gone from ItemDefs schema!
        cur.execute("""
            UPDATE ItemDefs
            SET Stackable = 1,
                MaxStackSize = ?
            WHERE (Stackable = 0 OR (Stackable = 1 AND MaxStackSize IN (1, 10, 40, ?)))
              AND Categories NOT IN (0, 32)
              AND Name NOT LIKE '%Full Helm%'
              AND (Components IS NULL OR (
                   Components NOT LIKE '%EquippableComponent%'
                   AND Components NOT LIKE '%PouchComponent%'
                   AND Components NOT LIKE '%YarnDialogueComponent%'
                   AND Components NOT LIKE '%ImageDisplayComponent%'
              ))
        """, (NEW_STACK_SIZE, NEW_STACK_SIZE))

        # 3. Totem cleansing buff (if multiplier > 1.0)
        if TOTEM_CLEANSE_MULTIPLIER > 1.0:
            for name, base_val in TOTEM_BASES.items():
                cur.execute("SELECT Id, Components FROM ItemDefs WHERE Name = ?", (name,))
                for row_id, comp in cur.fetchall():
                    if comp and '"CurseGain"' in comp:
                        new_val = int(round(base_val * TOTEM_CLEANSE_MULTIPLIER))
                        new_comp = re.sub(r'"CurseGain"\s*:\s*-[0-9]+', f'"CurseGain": {new_val}', comp)
                        cur.execute("UPDATE ItemDefs SET Components = ? WHERE Id = ?", (new_comp, row_id))

        conn.commit()
        conn.close()
        print(f"Stack Mod applied to {os.path.basename(db_path)}")

def apply_curse_mod():
    target_dbs = [
        os.path.join(EVERLAST_DIR, r"Assets\Database\Definitions\ComponentSetDefs.db"),
        os.path.join(EVERLAST_DIR, r"Assets\Database\Definitions\AbilityDefs.db"),
        os.path.join(EVERLAST_DIR, r"Everlast_Data\StreamingAssets\Server\Windows\Raptor.Data\Raptor.Game.db")
    ]
    for db in target_dbs:
        if not os.path.exists(db):
            continue
        conn = sqlite3.connect(db)
        cur = conn.cursor()

        # AbilityDefs (attacks, spells, weapon swings)
        if REMOVE_COMBAT_CURSE:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AbilityDefs'")
            if cur.fetchone():
                cur.execute("UPDATE AbilityDefs SET CurseGainOnUse = 0 WHERE CurseGainOnUse != 0")

        # ComponentSetDefs (gathering, mining, tree chopping, stealing)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ComponentSetDefs'")
        if cur.fetchone():
            cur.execute("SELECT Id, Components FROM ComponentSetDefs WHERE Components LIKE '%CurseGainOn%'")
            for id_, comp in cur.fetchall():
                new_comp = comp
                if REMOVE_GATHERING_CURSE:
                    new_comp = re.sub(r'"CurseGainOnSuccess"\s*:\s*[0-9]+', '"CurseGainOnSuccess": 0', new_comp)
                if REMOVE_STEALING_CURSE:
                    new_comp = re.sub(r'"CurseGainOnCollect"\s*:\s*[0-9]+', '"CurseGainOnCollect": 0', new_comp)
                # Ensure crafting remains 0 as well
                new_comp = re.sub(r'"CurseGainOnCraft"\s*:\s*[0-9]+', '"CurseGainOnCraft": 0', new_comp)
                if new_comp != comp:
                    cur.execute("UPDATE ComponentSetDefs SET Components = ? WHERE Id = ?", (new_comp, id_))

        conn.commit()
        conn.close()
        print(f"Curse Mod applied to {os.path.basename(db)}")

def main():
    print("=" * 60)
    print(" Everlast: Undying Tale - Quality of Life & Balance Patcher")
    print(" Compatible with build 1389+ (Post-Patch Schema)")
    print("=" * 60)
    if ENABLE_STACKING:
        apply_stack_mod()
    if REMOVE_GATHERING_CURSE or REMOVE_COMBAT_CURSE or REMOVE_STEALING_CURSE:
        apply_curse_mod()
    print("\n[SUCCESS] All mods successfully applied directly to game files!")
    print("=" * 60)

if __name__ == "__main__":
    main()
