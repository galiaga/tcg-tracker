from backend.models import Commander
import json
import os

def seed_commanders(db):
    if Commander.query.first():
        print("🔸 Commanders ya están insertados.")
        return

    path = "local_commanders.txt"
    if not os.path.exists(path):
        print("❌ No se encontró 'local_commanders.txt'")
        return

    with open(path, encoding="utf-8") as f:
        commanders = json.load(f)

    objects = []
    for c in commanders:
        obj = Commander(
            scryfall_id=c["scryfall_id"],
            name=c["name"],
            flavor_name=c.get("flavor_name"),
            mana_cost=c.get("mana_cost"),
            type_line=c.get("type_line"),
            oracle_text=c.get("oracle_text"),
            power=c.get("power"),
            toughness=c.get("toughness"),
            loyalty=c.get("loyalty"),
            colors=c.get("colors"),
            color_identity=c.get("color_identity"),
            set_code=c.get("set_code"),
            image_url=c.get("image_url"),
            art_crop=c.get("art_crop"),
            partner=c.get("partner", False),
            background=c.get("background", False),
            choose_a_background=c.get("choose_a_background", False),
            friends_forever=c.get("friends_forever", False),
            doctor_companion=c.get("doctor_companion", False),
            time_lord_doctor=c.get("time_lord_doctor", False),
        )
        objects.append(obj)

    db.session.add_all(objects)
    db.session.commit()
    print(f"✅ {len(objects)} commanders insertados.")
