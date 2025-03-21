"""Remove duplicate foreign key from commander_decks

Revision ID: fa7d0523e1bf
Revises: f2eb62c4fa46
Create Date: 2025-03-20 16:04:27.030682

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fa7d0523e1bf'
down_revision = 'f2eb62c4fa46'

def upgrade():
    # Crear una nueva tabla sin la restricción duplicada
    op.create_table(
        'new_commander_decks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('deck_id', sa.Integer(), sa.ForeignKey('decks.id'), nullable=False),
        sa.Column('commander_id', sa.Integer(), sa.ForeignKey('commanders.id'), nullable=False),
        sa.Column('associated_commander_id', sa.Integer(), nullable=True),  # Sin ForeignKey aún
        sa.Column('relationship_type', sa.String(), nullable=True),
    )

    # Copiar datos de la tabla antigua a la nueva
    op.execute('''
        INSERT INTO new_commander_decks (id, deck_id, commander_id, associated_commander_id, relationship_type)
        SELECT id, deck_id, commander_id, associated_commander_id, relationship_type FROM commander_decks
    ''')

    # Eliminar la tabla original
    op.drop_table('commander_decks')

    # Renombrar la nueva tabla
    op.rename_table('new_commander_decks', 'commander_decks')

    # Agregar la ForeignKeyConstraint manualmente con nombre explícito
    op.create_foreign_key(
        "fk_associated_commander",
        "commander_decks",
        "commanders",
        ["associated_commander_id"],
        ["id"]
    )

def downgrade():
    pass  # Puedes implementar el downgrade si es necesario
