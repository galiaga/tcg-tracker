import requests
import sqlite3
import time

# Conectar a la base de datos SQLite
conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

# Definir la URL base de la API de Scryfall
base_url = 'https://api.scryfall.com/cards/search?q=is:commander+not:digital'

# Inicializar variables
next_page = base_url  # Primera solicitud a la URL base
count_inserted = 0

while next_page:
    response = requests.get(next_page)
    
    if response.status_code != 200:
        print(f"❌ Error al obtener datos de Scryfall: {response.status_code}")
        break  # Detener ejecución si ocurre un error

    data = response.json()
    
    for card in data["data"]:
        scryfall_id = card.get("id", "")
        name = card.get("name", "")
        flavor_name = card.get("flavor_name", None)  # Nuevo campo
        mana_cost = card.get("mana_cost", "")
        type_line = card.get("type_line", "")
        oracle_text = card.get("oracle_text", "")
        power = card.get("power", None)  # Asegurar que se guarde
        toughness = card.get("toughness", None)  # Asegurar que se guarde
        loyalty = card.get("loyalty", None)  # Asegurar que se guarde
        colors = ",".join(card.get("colors", []))
        color_identity = ",".join(card.get("color_identity", []))
        set_code = card.get("set", "")  # Cambiar "set_name" por "set"
        image_url = card.get("image_uris", {}).get("normal", "")
        art_crop = card.get("image_uris", {}).get("art_crop", None)  # Obtener art_crop

        cursor.execute("""
            INSERT INTO commanders (scryfall_id, name, flavor_name, mana_cost, type_line, oracle_text, 
                power, toughness, loyalty, colors, color_identity, set_code, image_url, art_crop, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scryfall_id) DO UPDATE SET 
                name=excluded.name, flavor_name=excluded.flavor_name, mana_cost=excluded.mana_cost, 
                type_line=excluded.type_line, oracle_text=excluded.oracle_text, 
                power=excluded.power, toughness=excluded.toughness, loyalty=excluded.loyalty,
                colors=excluded.colors, color_identity=excluded.color_identity, 
                set_code=excluded.set_code, image_url=excluded.image_url, 
                art_crop=excluded.art_crop, updated_at=CURRENT_TIMESTAMP

        """, (scryfall_id, name, flavor_name, mana_cost, type_line, oracle_text, 
              power, toughness, loyalty, colors, color_identity, set_code, image_url, art_crop))
        
        count_inserted += 1

    conn.commit()

    # Mover a la siguiente página si está disponible
    next_page = data.get("next_page", None)

    # Pequeña pausa para respetar los límites de la API de Scryfall
    time.sleep(0.1)

# Cerrar conexión con la base de datos
conn.close()

print(f"✅ Base de datos actualizada. Comandantes insertados/actualizados: {count_inserted}.")
