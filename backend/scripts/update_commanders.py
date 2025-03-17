import requests
import sqlite3
import time

# Connect to the SQLite database
conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

# Define the base URL for the Scryfall API
base_url = 'https://api.scryfall.com/cards/search?q=is:commander+not:digital'

# Initialize variables
next_page = base_url  # First request goes to the base URL
count_inserted = 0

while next_page:
    response = requests.get(next_page)
    
    if response.status_code != 200:
        print(f"Error fetching data from Scryfall: {response.status_code}")
        break  # Stop execution if an error occurs

    data = response.json()
    
    for card in data["data"]:
        scryfall_id = card.get("id", "")
        name = card.get("name", "")
        mana_cost = card.get("mana_cost", "")
        type_line = card.get("type_line", "")
        oracle_text = card.get("oracle_text", "")
        colors = ",".join(card.get("colors", []))
        color_identity = ",".join(card.get("color_identity", []))
        image_url = card.get("image_uris", {}).get("normal", "")

        cursor.execute("""
            INSERT INTO commanders (scryfall_id, name, mana_cost, type_line, oracle_text, 
                colors, color_identity, image_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scryfall_id) DO UPDATE SET 
                name=excluded.name, mana_cost=excluded.mana_cost, type_line=excluded.type_line,
                oracle_text=excluded.oracle_text, colors=excluded.colors, 
                color_identity=excluded.color_identity, image_url=excluded.image_url, 
                updated_at=CURRENT_TIMESTAMP
        """, (scryfall_id, name, mana_cost, type_line, oracle_text, colors, color_identity, image_url))
        
        count_inserted += 1

    conn.commit()

    # Move to the next page if available
    next_page = data.get("next_page", None)

    # Sleep to respect Scryfall API rate limits (recommended delay)
    time.sleep(0.1)

# Close the database connection
conn.close()

print(f"Commander database successfully updated. Inserted/Updated {count_inserted} records.")
