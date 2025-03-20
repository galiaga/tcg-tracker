import sqlite3

# Conectar a la base de datos SQLite
conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

# Actualizar partner
cursor.execute("""
    UPDATE commanders
    SET partner = 1
    WHERE oracle_text LIKE '%Partner%';
""")

# Actualizar background
cursor.execute("""
    UPDATE commanders
    SET background = 1
    WHERE oracle_text LIKE '%Background%';
""")

# Actualizar friends_forever
cursor.execute("""
    UPDATE commanders
    SET friends_forever = 1
    WHERE oracle_text LIKE '%Friends Forever%';
""")

# Actualizar doctor_companion asegurando que las comillas sean correctas
cursor.execute("""
    UPDATE commanders
    SET doctor_companion = 1
    WHERE REPLACE(oracle_text, '’', "'") LIKE '%Doctor''s companion%';
""")

# Actualizar Time Lord Doctor
cursor.execute("""
    UPDATE commanders
    SET time_lord_doctor = 1
    WHERE type_line LIKE '%Time Lord Doctor%';
""")

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("✅ Partner, Background, Friends Forever y Doctor’s Companion actualizados correctamente.")
