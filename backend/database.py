import os
import sqlite3
from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "app.db")

def get_db():
    # Abre una conexión a la db si es que no existe en g
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Para devolver resultados como diccionarios
    return g.db

def close_db(exception):
    #Cierra la conexión a la base de datos si existe en g
    db = g.pop("db", None)
    if db is not None:
        db.close()