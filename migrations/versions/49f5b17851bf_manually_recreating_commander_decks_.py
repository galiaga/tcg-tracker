"""Manually recreating commander_decks with associated_commander_id

Revision ID: 49f5b17851bf
Revises: 1297646eae00
Create Date: 2025-03-20 16:14:21.561078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49f5b17851bf'
down_revision = '1297646eae00'

def upgrade():
    # Crear una nueva tabla con todas las claves foráneas correctas
    op.create_table(
        "new_commander_decks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deck_id", sa.Integer(), sa.ForeignKey("decks.id"), nullable=False),
        sa.Column("commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=False),
        sa.Column("associated_commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=True),
        sa.Column("relationship_type", sa.String(), nullable=True),
    )

    # Copiar los datos de la tabla antigua a la nueva
    op.execute('''
        INSERT INTO new_commander_decks (id, deck_id, commander_id, associated_commander_id, relationship_type)
        SELECT id, deck_id, commander_id, associated_commander_id, relationship_type FROM commander_decks
    ''')

    # Eliminar la tabla antigua
    op.drop_table("commander_decks")

    # Renombrar la nueva tabla a "commander_decks"
    op.rename_table("new_commander_decks", "commander_decks")

def downgrade():
    op.drop_table("commander_decks")