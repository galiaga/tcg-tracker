import os
import time
import requests
import click
from backend import db
from sqlalchemy import func, update

try:
    from backend.models import DeckType, Commander
except ImportError:
    print("Error: models not imported")
    exit()

DECK_TYPE_NAMES = [
    "Standard",
    "Pioneer",
    "Modern",
    "Legacy",
    "Vintage",
    "Pauper",
    "Commander / EDH"
]

@click.command("seed-deck-types")
def seed_deck_types():
    """Seeds the database with standard TCG deck types."""
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


@click.command("update-commanders")
def update_commanders_data():
    """Fetches and updates commander data from Scryfall."""
    print("Connecting using Flask-SQLAlchemy context...")
    base_url = 'https://api.scryfall.com/cards/search?q=is:commander+not:digital'
    next_page = base_url
    count_processed = 0
    count_added = 0
    count_updated = 0
    page_count = 0

    print("Starting Scryfall commander update...")
    while next_page:
        page_count += 1
        data = {}
        try:
            print(f"Fetching Page {page_count}: {next_page[:70]}...")
            response = requests.get(next_page, timeout=30)
            response.raise_for_status()
            data = response.json()
            cards_in_page = data.get("data", [])
            if not cards_in_page:
                print("No cards found in page data. Ending.")
                break

            print(f"Processing {len(cards_in_page)} cards from page {page_count}...")
            page_added = 0
            page_updated = 0

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
                image_uris = card_data.get("image_uris", {}) 
                image_url = image_uris.get("normal") if image_uris else None
                art_crop = image_uris.get("art_crop") if image_uris else None

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
                    page_updated += 1
                else:
                    new_commander = Commander(
                        scryfall_id=scryfall_id,
                        name=name,
                        flavor_name=flavor_name,
                        mana_cost=mana_cost,
                        type_line=type_line,
                        oracle_text=oracle_text,
                        power=power,
                        toughness=toughness,
                        loyalty=loyalty,
                        colors=colors,
                        color_identity=color_identity,
                        set_code=set_code,
                        image_url=image_url,
                        art_crop=art_crop
                    )
                    db.session.add(new_commander)
                    page_added += 1
                count_processed += 1

            db.session.commit()
            count_added += page_added
            count_updated += page_updated
            print(f"Page {page_count} committed. Added this page: {page_added}, Updated this page: {page_updated}")

        except requests.exceptions.RequestException as e:
            print(f"Scryfall request error on page {page_count}: {e}")
            print("Stopping update.")
            break
        except Exception as e:
            print(f"Error processing/saving data on page {page_count}: {e}")
            db.session.rollback()
            print("Stopping update due to processing error.")
            break
        finally:
             next_page = data.get("next_page", None)
             if next_page:
                  print("Waiting 100ms before next page...")
                  time.sleep(0.1)
             else:
                 print("No next_page URL found. Update should be complete.")


    print(f"Finished commander update. Total Processed: {count_processed}. Total Added: {count_added}, Total Updated: {count_updated}")


@click.command("update-flags")
def update_flags():
    """Updates boolean flags on Commander records based on oracle text or type line."""
    print("Updating commander flags...")
    try:
        print("Updating 'partner' flag...")
        stmt_partner = update(Commander).where(
            Commander.oracle_text.like('%Partner%')
        ).values(partner=True)
        result_partner = db.session.execute(stmt_partner)
        print(f"Rows potentially affected by partner update: {result_partner.rowcount}")

        print("Updating 'background' flag...")
        stmt_bg = update(Commander).where(
            Commander.type_line == 'Legendary Enchantment — Background'
        ).values(background=True)
        result_bg = db.session.execute(stmt_bg)
        print(f"Rows potentially affected by background update: {result_bg.rowcount}")

        print("Updating 'friends_forever' flag...")
        stmt_ff = update(Commander).where(
            func.lower(Commander.oracle_text).like('%friends forever%')
        ).values(friends_forever=True)
        result_ff = db.session.execute(stmt_ff)
        print(f"Rows potentially affected by friends_forever update: {result_ff.rowcount}")

        print("Updating 'doctor_companion' flag...")
        normalized_text_dc = func.replace(Commander.oracle_text, '’', "'")
        pattern_dc = '%Doctor\'s companion%'
        stmt_dc = update(Commander).where(
            normalized_text_dc.ilike(pattern_dc)
        ).values(doctor_companion=True)
        result_dc = db.session.execute(stmt_dc)
        print(f"Rows potentially affected by doctor_companion update: {result_dc.rowcount}")

        print("Updating 'time_lord_doctor' flag...")
        stmt_tld = update(Commander).where(
            Commander.type_line.ilike('%Time Lord Doctor%')
        ).values(time_lord_doctor=True)
        result_tld = db.session.execute(stmt_tld)
        print(f"Rows potentially affected by time_lord_doctor update: {result_tld.rowcount}")

        print("Updating 'choose_a_background' flag...")
        stmt_cab = update(Commander).where(
            func.lower(Commander.oracle_text).like('%choose a background%')
        ).values(choose_a_background=True)
        result_cab = db.session.execute(stmt_cab)
        print(f"Rows potentially affected by choose_a_background update: {result_cab.rowcount}")

        print("Committing flag updates...")
        db.session.commit()
        print("✅ Commander flags updated successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"ERROR updating flags: {e}")