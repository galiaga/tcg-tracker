"""Adding associated_commander_id column

Revision ID: 3f8e9d27863d
Revises: edce912531a6
Create Date: 2025-03-20 16:17:06.344056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f8e9d27863d'
down_revision = 'edce912531a6'

def upgrade():
    # Agregar la columna `associated_commander_id` con la clave foránea
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.add_column(sa.Column("associated_commander_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_associated_commander",
            "commander_decks",
            "commanders",
            ["associated_commander_id"],
            ["id"]
        )

def downgrade():
    # Remover la columna y la clave foránea en caso de rollback
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.drop_constraint("fk_associated_commander", type_="foreignkey")
        batch_op.drop_column("associated_commander_id")
