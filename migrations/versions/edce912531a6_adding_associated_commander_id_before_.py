"""Adding associated_commander_id before recreation

Revision ID: edce912531a6
Revises: 49f5b17851bf
Create Date: 2025-03-20 16:15:20.640194

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edce912531a6'
down_revision = '49f5b17851bf'

def upgrade():
    # 1️⃣ Primero, agregamos la columna `associated_commander_id` a la tabla existente
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.add_column(sa.Column("associated_commander_id", sa.Integer(), nullable=True))

    # 2️⃣ Luego, recreamos la tabla con la clave foránea correcta
    op.create_table(
        "new_commander_decks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deck_id", sa.Integer(), sa.ForeignKey("decks.id"), nullable=False),
        sa.Column("commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=False),
        sa.Column("associated_commander_id", sa.Integer(), sa.ForeignKey("commanders.id"), nullable=True),
        sa.Column("relationship_type", sa.String(), nullable=True),
    )

    # 3️⃣ Copiamos los datos de la tabla antigua a la nueva
    op.execute('''
        INSERT INTO new_commander_decks (id, deck_id, commander_id, associated_commander_id, relationship_type)
        SELECT id, deck_id, commander_id, associated_commander_id, relationship_type FROM commander_decks
    ''')

    # 4️⃣ Eliminamos la tabla antigua
    op.drop_table("commander_decks")

    # 5️⃣ Renombramos la nueva tabla a "commander_decks"
    op.rename_table("new_commander_decks", "commander_decks")

def downgrade():
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.drop_column("associated_commander_id")