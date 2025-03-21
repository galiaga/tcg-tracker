"""Adding associated_commander_id column first

Revision ID: 449d1f757d0f
Revises: 3f8e9d27863d
Create Date: 2025-03-20 16:18:13.975241

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '449d1f757d0f'
down_revision = '3f8e9d27863d'

def upgrade():
    # 1️⃣ Agregar la columna a commander_decks antes de copiar datos
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.add_column(sa.Column("associated_commander_id", sa.Integer(), nullable=True))

    # 2️⃣ Crear una nueva tabla con todas las claves foráneas correctas
    op.create_table(
        "new_commander_decks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deck_id", sa.Integer(), sa.ForeignKey("decks.id"), nullable=False),
        sa.Column("commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=False),
        sa.Column("associated_commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=True),
        sa.Column("relationship_type", sa.String(), nullable=True),
    )

    # 3️⃣ Copiar los datos de la tabla antigua a la nueva
    op.execute('''
        INSERT INTO new_commander_decks (id, deck_id, commander_id, associated_commander_id, relationship_type)
        SELECT id, deck_id, commander_id, associated_commander_id, relationship_type FROM commander_decks
    ''')

    # 4️⃣ Eliminar la tabla antigua
    op.drop_table("commander_decks")

    # 5️⃣ Renombrar la nueva tabla a "commander_decks"
    op.rename_table("new_commander_decks", "commander_decks")

def downgrade():
    # Si necesitas hacer rollback, eliminar la columna
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.drop_column("associated_commander_id")
