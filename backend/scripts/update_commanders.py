import requests
import psycopg2
import time
import os
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    raise ValueError("Error: La variable de entorno DATABASE_URL no está definida.")

# Adaptar URL si usa postgres:// en lugar de postgresql:// (psycopg2 a veces lo necesita)
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

conn = None
cursor = None

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    print("Conectado a PostgreSQL...")

    base_url = 'https://api.scryfall.com/cards/search?q=is:commander+not:digital'
    next_page = base_url
    count_processed = 0
    count_inserted_updated = 0

    print("Empezando a obtener y procesar comandantes desde Scryfall...")
    while next_page:
        print(f"Obteniendo página: {next_page}")
        response = requests.get(next_page)

        if response.status_code != 200:
            print(f"Error al obtener datos de Scryfall: {response.status_code}")
            break

        data = response.json()
        cards_in_page = data.get("data", [])
        if not cards_in_page:
            print("No se encontraron cartas en la página.")
            break

        print(f"Procesando {len(cards_in_page)} cartas...")
        for card in cards_in_page:
            scryfall_id = card.get("id", "")
            name = card.get("name", "")
            flavor_name = card.get("flavor_name", None)
            mana_cost = card.get("mana_cost", "")
            type_line = card.get("type_line", "")
            oracle_text = card.get("oracle_text", "")
            power = card.get("power", None)
            toughness = card.get("toughness", None)
            loyalty = card.get("loyalty", None)
            colors = ",".join(card.get("colors", []))
            color_identity = ",".join(card.get("color_identity", []))
            set_code = card.get("set", "")
            image_url = card.get("image_uris", {}).get("normal", None)
            art_crop = card.get("image_uris", {}).get("art_crop", None)

            sql = """
                INSERT INTO commanders (
                    scryfall_id, name, flavor_name, mana_cost, type_line, oracle_text,
                    power, toughness, loyalty, colors, color_identity, set_code, image_url,
                    art_crop, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT(scryfall_id) DO UPDATE SET
                    name=excluded.name, flavor_name=excluded.flavor_name, mana_cost=excluded.mana_cost,
                    type_line=excluded.type_line, oracle_text=excluded.oracle_text,
                    power=excluded.power, toughness=excluded.toughness, loyalty=excluded.loyalty,
                    colors=excluded.colors, color_identity=excluded.color_identity,
                    set_code=excluded.set_code, image_url=excluded.image_url,
                    art_crop=excluded.art_crop, updated_at=CURRENT_TIMESTAMP;
            """
            params = (
                scryfall_id, name, flavor_name, mana_cost, type_line, oracle_text,
                power, toughness, loyalty, colors, color_identity, set_code, image_url, art_crop
            )
            cursor.execute(sql, params)
            count_processed += 1
            if cursor.rowcount > 0:
                 count_inserted_updated += 1

        conn.commit()
        print(f"Progreso guardado. {count_inserted_updated} registros insertados/actualizados hasta ahora.")

        next_page = data.get("next_page", None)
        if next_page:
            print("Esperando antes de la siguiente página...")
            time.sleep(0.1)

    print(f"Proceso Scryfall completado. Total de cartas procesadas: {count_processed}.")
    print(f"Total de comandantes insertados/actualizados: {count_inserted_updated}.")

except psycopg2.Error as e:
    print(f"Error de PostgreSQL: {e}")
    if conn:
        conn.rollback()
except requests.exceptions.RequestException as e:
     print(f"Error de Red (requests): {e}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
    if conn:
        conn.rollback()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("Conexión a PostgreSQL cerrada.")