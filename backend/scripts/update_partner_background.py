import psycopg2
import os

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    raise ValueError("Error: La variable de entorno DATABASE_URL no está definida.")

if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

conn = None
cursor = None

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    print("Conectado a PostgreSQL...")

    print("Actualizando 'partner'...")
    cursor.execute("""
        UPDATE commanders
        SET partner = TRUE
        WHERE oracle_text LIKE '%Partner%';
    """)
    print(f"Filas afectadas por partner: {cursor.rowcount}")

    print("Actualizando 'background'...")
    cursor.execute("""
        UPDATE commanders
        SET background = TRUE
        WHERE type_line = 'Legendary Enchantment — Background';
    """)
    print(f"Filas afectadas por background: {cursor.rowcount}")

    print("Actualizando 'friends_forever'...")
    cursor.execute("""
        UPDATE commanders
        SET friends_forever = TRUE
        WHERE oracle_text LIKE '%Friends Forever%';
    """)
    print(f"Filas afectadas por friends_forever: {cursor.rowcount}")

    print("Actualizando 'doctor_companion'...")
    cursor.execute("""
        UPDATE commanders
        SET doctor_companion = TRUE
        WHERE REPLACE(oracle_text, '’', '''') LIKE '%Doctor''s companion%';
    """)
    print(f"Filas afectadas por doctor_companion: {cursor.rowcount}")

    print("Actualizando 'time_lord_doctor'...")
    cursor.execute("""
        UPDATE commanders
        SET time_lord_doctor = TRUE
        WHERE type_line LIKE '%Time Lord Doctor%';
    """)
    print(f"Filas afectadas por time_lord_doctor: {cursor.rowcount}")

    print("Actualizando 'choose_a_background'...")
    cursor.execute("""
        UPDATE commanders
        SET choose_a_background = TRUE
        WHERE oracle_text LIKE '%Choose a Background%';
    """)
    print(f"Filas afectadas por choose_a_background: {cursor.rowcount}")

    conn.commit()
    print("✅ Partner, Background, Friends Forever, etc., actualizados correctamente.")

except psycopg2.Error as e:
    print(f"Error de PostgreSQL: {e}")
    if conn:
        conn.rollback()
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