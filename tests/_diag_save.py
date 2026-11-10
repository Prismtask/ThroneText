"""Diagnose savegame_1.json structure (read-only)."""
import json

PATH = "savefile/savegame_1.json"
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("== top-level heroine flags ==")
for key in ("wl_alice_state", "wl_redhood_state", "wl_dorothy_state",
            "wonderland_heroine_alice_permanent",
            "wonderland_heroine_redhood_permanent",
            "wonderland_heroine_dorothy_permanent",
            "wonderland_saved_temp_heroines", "wonderland_active",
            "palette_recruited", "palette_recruit_declined"):
    if key in data:
        print(f"  {key} = {data[key]!r}")

print("\n== allies ==")
for i, ally in enumerate(data.get("allies", [])):
    eq = {s: (ally.get("equipped", {}).get(s) or {}).get("id")
          for s in ("weapon", "armor", "accessory1", "accessory2")}
    print(f"  [{i}] {ally.get('name')!r} key={ally.get('key')!r} lvl={ally.get('level')} "
          f"hk={ally.get('_heroine_key')!r} temp={ally.get('_wonderland_temp')!r} "
          f"cap={ally.get('level_cap')} aff={ally.get('affection')} exp={ally.get('exp')}")
    print(f"      eq={eq} inn={ally.get('innate_skills')} learned={ally.get('learned_skills')} "
          f"mastery={dict(ally.get('skill_mastery') or {})}")
    extra = {k: v for k, v in ally.items()
             if k.startswith("_") and k not in ("_heroine_key", "_wonderland_temp",
                                                "_heroine_passive", "_heroine_permanent_passive")}
    if extra:
        print(f"      extra={extra}")

print("\n== party_order ==")
print(" ", data.get("party_order"))

print("\n== benched ==")
for i, ally in enumerate(data.get("wonderland_benched_allies", [])):
    print(f"  [{i}] {ally.get('name')!r} key={ally.get('key')!r} hk={ally.get('_heroine_key')!r}")

print("\n== houses ==")
for city_id, house in data.get("houses", {}).items():
    girls = house.get("monster_girls", [])
    heroines = [g for g in girls if g.get("key", "").startswith("wonderland_")]
    print(f"  {city_id}: {len(girls)} girls, heroine entries: "
          f"{[(g.get('name'), g.get('level')) for g in heroines]}")

print("\n== inventory quest items ==")
for item in data.get("inventory", []):
    if item.get("id") in ("grandmothers_axe", "ruby_slippers", "silver_slippers",
                          "woodcutters_broken_axe", "vorpal_blade", "vorpal_blade_rusted",
                          "witch_hat", "emerald_flame_crystal"):
        print(f"  {item.get('id')!r} name={item.get('name')!r} enhance={item.get('enhance')}")

print("\n== wl flags ==")
for key in sorted(data):
    if key.startswith("wl_") or key.startswith("wonderland"):
        val = data[key]
        if isinstance(val, (list, dict)):
            print(f"  {key} = <{type(val).__name__} len={len(val)}>")
        elif key != "wonderland_saved_temp_heroines":
            print(f"  {key} = {val!r}")
