import sqlite3

conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

cursor.execute("""
    UPDATE commanders
    SET partner = 1
    WHERE oracle_text LIKE '%Partner%';
""")

cursor.execute("""
    UPDATE commanders
    SET background = 1
    WHERE type_line IS 'Legendary Enchantment — Background';
""")

cursor.execute("""
    UPDATE commanders
    SET friends_forever = 1
    WHERE oracle_text LIKE '%Friends Forever%';
""")

cursor.execute("""
    UPDATE commanders
    SET doctor_companion = 1
    WHERE REPLACE(oracle_text, '’', "'") LIKE '%Doctor''s companion%';
""")

cursor.execute("""
    UPDATE commanders
    SET time_lord_doctor = 1
    WHERE type_line LIKE '%Time Lord Doctor%';
""")

cursor.execute("""
    UPDATE commanders
    SET choose_a_background = 1
    WHERE oracle_text LIKE '%Choose a Background%';
""")

conn.commit()
conn.close()

print("✅ Partner, Background, Friends Forever y Doctor’s Companion actualizados correctamente.")
