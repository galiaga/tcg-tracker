# backend/database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})