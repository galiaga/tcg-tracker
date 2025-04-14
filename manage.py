import os
import time
import requests
from backend import create_app, db 
from flask_migrate import Migrate 
from sqlalchemy import text


try:
    from backend.models import DeckType, Commander
except ImportError:
    print("Error: No se pudieron importar los modelos. Asegúrate de que existan y la ruta sea correcta.")
    print("Ejemplo esperado: backend/models/deck_type.py con clase DeckType")
    print("Ejemplo esperado: backend/models/commander.py con clase Commanders")
    exit() 

app = create_app(os.environ.get('FLASK_ENV'))

migrate = Migrate(app, db)

DECK_TYPE_NAMES = [
    "Standard",
    "Pioneer",
    "Modern",
    "Legacy",
    "Vintage",
    "Pauper",
    "Commander / EDH"
]

@app.cli.command("seed-deck-types")
def seed_deck_types():
    print("Seeding deck types...")
    count = 0
    try:
        for name in DECK_TYPE_NAMES:
            existing_type = db.session.execute(
                db.select(DeckType).filter_by(name=name)
            ).scalar_one_or_none()

            if not existing_type:
                new_deck_type = DeckType(name=name)
                db.session.add(new_deck_type)
                print(f"  + Adding DeckType: {name}")
                count += 1
            else:
                print(f"  = DeckType '{name}' already exists, skipping.")

        if count > 0:
            db.session.commit()
            print(f"Successfully added {count} new deck types.")
        else:
            print("No new deck types to add.")
        print("Deck type seeding finished.")
    except Exception as e:
        db.session.rollback()
        print(f"ERROR seeding deck types: {e}")

@app.cli.command("update-commanders")
def update_commanders_data():
    print("Connecting using Flask-SQLAlchemy context...")
    base_url = 'https://api.scryfall.com/cards/search?q=is:commander+not:digital'
    next_page = base_url
    count_processed = 0
    count_added = 0
    count_updated = 0

    print("Starting Scryfall commander update...")
    while next_page:
        data = {} 
        try:
            print(f"Fetching: {next_page[:70]}...")
            response = requests.get(next_page, timeout=20)
            response.raise_for_status()
            data = response.json()
            cards_in_page = data.get("data", [])
            if not cards_in_page: break

            print(f"Processing {len(cards_in_page)} cards...")
            with app.app_context():
                for card_data in cards_in_page:
                    scryfall_id = card_data.get("id")
                    if not scryfall_id: continue

                    existing_commander = db.session.execute(
                        db.select(Commander).filter_by(scryfall_id=scryfall_id)
                    ).scalar_one_or_none()

                    name = card_data.get("name", "")
                    flavor_name = card_data.get("flavor_name", None)
                    mana_cost = card_data.get("mana_cost", "")
                    type_line = card_data.get("type_line", "")
                    oracle_text = card_data.get("oracle_text", "")
                    power = card_data.get("power", None)
                    toughness = card_data.get("toughness", None)
                    loyalty = card_data.get("loyalty", None)
                    colors = ",".join(card_data.get("colors", []))
                    color_identity = ",".join(card_data.get("color_identity", []))
                    set_code = card_data.get("set", "")
                    image_url = card_data.get("image_uris", {}).get("normal")
                    art_crop = card_data.get("image_uris", {}).get("art_crop")

                    if existing_commander:
                        existing_commander.name = name
                        existing_commander.flavor_name = flavor_name
                        existing_commander.mana_cost = mana_cost
                        existing_commander.type_line = type_line
                        existing_commander.oracle_text = oracle_text
                        existing_commander.power = power
                        existing_commander.toughness = toughness
                        existing_commander.loyalty = loyalty
                        existing_commander.colors = colors
                        existing_commander.color_identity = color_identity
                        existing_commander.set_code = set_code
                        existing_commander.image_url = image_url
                        existing_commander.art_crop = art_crop
                        count_updated += 1
                    else:
                        # Insertar
                        new_commander = Commander(
                            scryfall_id=scryfall_id, name=name, flavor_name=flavor_name,
                            mana_cost=mana_cost, type_line=type_line, oracle_text=oracle_text,
                            power=power, toughness=toughness, loyalty=loyalty, colors=colors,
                            color_identity=color_identity, set_code=set_code,
                            image_url=image_url, art_crop=art_crop
                        )
                        db.session.add(new_commander)
                        count_added += 1
                    count_processed += 1

                db.session.commit()
                print(f"Page committed. Added: {count_added}, Updated: {count_updated}")

        except requests.exceptions.RequestException as e:
            print(f"Scryfall request error: {e}")
            break
        except Exception as e:
            print(f"Error processing/saving data: {e}")
            db.session.rollback()
        finally:
             next_page = data.get("next_page", None)
             if next_page:
                  print("Waiting 100ms...")
                  time.sleep(0.1)

    print(f"Finished commander update. Total Processed: {count_processed}. Added: {count_added}, Updated: {count_updated}")


@app.cli.command("update-flags")
def update_flags():
    print("Updating commander flags...")
    try:
        with app.app_context():
            print("Updating 'partner'...")
            stmt_partner = db.update(Commander).where(Commander.oracle_text.like('%Partner%')).values(partner=True)
            result_partner = db.session.execute(stmt_partner)
            print(f"Rows affected by partner: {result_partner.rowcount}")

            print("Updating 'background'...")
            stmt_bg = db.update(Commander).where(Commander.type_line == 'Legendary Enchantment — Background').values(background=True)
            result_bg = db.session.execute(stmt_bg)
            print(f"Rows affected by background: {result_bg.rowcount}")

            print("Updating 'friends_forever'...")
            stmt_ff = db.update(Commander).where(Commander.oracle_text.like('%Friends Forever%')).values(friends_forever=True)
            result_ff = db.session.execute(stmt_ff)
            print(f"Rows affected by friends_forever: {result_ff.rowcount}")

            print("Updating 'doctor_companion'...")
            stmt_dc = db.update(Commander).where(db.func.replace(Commander.oracle_text, '’', "'").like('%Doctor''s companion%')).values(doctor_companion=True)
            result_dc = db.session.execute(stmt_dc)
            print(f"Rows affected by doctor_companion: {result_dc.rowcount}")

            print("Updating 'time_lord_doctor'...")
            stmt_tld = db.update(Commander).where(Commander.type_line.like('%Time Lord Doctor%')).values(time_lord_doctor=True)
            result_tld = db.session.execute(stmt_tld)
            print(f"Rows affected by time_lord_doctor: {result_tld.rowcount}")

            print("Updating 'choose_a_background'...")
            stmt_cab = db.update(Commander).where(Commander.oracle_text.like('%Choose a Background%')).values(choose_a_background=True)
            result_cab = db.session.execute(stmt_cab)
            print(f"Rows affected by choose_a_background: {result_cab.rowcount}")

            db.session.commit()
            print("✅ Commander flags updated successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"ERROR updating flags: {e}")