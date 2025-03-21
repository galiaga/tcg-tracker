from alembic import op
import sqlalchemy as sa

# IDs de las migraciones
revision = '1297646eae00'
down_revision = '41913ab291f1'

def upgrade():
    # Usar batch mode para recrear la tabla con la clave foránea correcta
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.create_foreign_key(
            "fk_associated_commander",
            "commanders",
            ["associated_commander_id"],
            ["id"]
        )

def downgrade():
    with op.batch_alter_table("commander_decks") as batch_op:
        batch_op.drop_constraint("fk_associated_commander", type_="foreignkey")
