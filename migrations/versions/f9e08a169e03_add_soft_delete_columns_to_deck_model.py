# migrations/versions/f9e08a169e03_add_soft_delete_columns_to_deck_model.py

"""Add soft delete columns to Deck model

Revision ID: f9e08a169e03
Revises: 5a3e126c5ace
Create Date: 2025-04-17 13:25:24.164329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9e08a169e03'
down_revision = '5a3e126c5ace' # Should point to the last successful migration
branch_labels = None
depends_on = None


def upgrade():
    # ### Modified Alembic commands - Focus only on 'decks' table ###
    print("Applying batch operations ONLY to 'decks' table for soft delete columns...")
    with op.batch_alter_table('decks', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            # Add server_default='1' for SQLite compatibility with NOT NULL
            server_default=sa.text('1')
        ))
        batch_op.add_column(sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True
        ))
        batch_op.create_index(
            batch_op.f('ix_decks_is_active'), # Use batch_op.f for auto-naming
            ['is_active'],
            unique=False
        )
    print("Batch operations for 'decks' table complete.")

    # --- REMOVED operations on match_tags, matches, user_decks ---
    # --- These were likely generated incorrectly due to previous migration edits ---
    # --- We assume the CASCADE constraints added previously should remain ---
    # --- Original incorrect blocks:
    # with op.batch_alter_table('match_tags', schema=None) as batch_op:
    #     batch_op.drop_constraint('match_tags_match_id_fkey_cascade', type_='foreignkey')
    #     batch_op.create_foreign_key(None, 'matches', ['match_id'], ['id'])
    # with op.batch_alter_table('matches', schema=None) as batch_op:
    #     batch_op.drop_constraint('matches_user_deck_id_fkey_cascade', type_='foreignkey') # Corrected name here
    #     batch_op.create_foreign_key(None, 'user_decks', ['user_deck_id'], ['id'])
    # with op.batch_alter_table('user_decks', schema=None) as batch_op:
    #     batch_op.drop_constraint('user_decks_deck_id_fkey_cascade', type_='foreignkey')
    #     batch_op.create_foreign_key(None, 'decks', ['deck_id'], ['id'])
    # --- End of removed blocks ---

    print("Upgrade complete for f9e08a169e03.")
    # ### end Modified Alembic commands ###


def downgrade():
    # ### Modified Alembic commands - Focus only on 'decks' table ###
    print("Reverting batch operations ONLY for 'decks' table...")
    with op.batch_alter_table('decks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_decks_is_active')) # Use batch_op.f
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('is_active')
    print("Batch revert operations for 'decks' table complete.")

    # --- REMOVED operations on match_tags, matches, user_decks ---
    # --- Original incorrect blocks:
    # with op.batch_alter_table('user_decks', schema=None) as batch_op:
    #     batch_op.drop_constraint(None, type_='foreignkey')
    #     batch_op.create_foreign_key('user_decks_deck_id_fkey_cascade', 'decks', ['deck_id'], ['id'], ondelete='CASCADE')
    # with op.batch_alter_table('matches', schema=None) as batch_op:
    #     batch_op.drop_constraint(None, type_='foreignkey')
    #     batch_op.create_foreign_key('matches_user_deck_id_fkey_cascade', 'user_decks', ['user_deck_id'], ['id'], ondelete='CASCADE') # Corrected name here
    # with op.batch_alter_table('match_tags', schema=None) as batch_op:
    #     batch_op.drop_constraint(None, type_='foreignkey')
    #     batch_op.create_foreign_key('match_tags_match_id_fkey_cascade', 'matches', ['match_id'], ['id'], ondelete='CASCADE')
    # --- End of removed blocks ---

    print("Downgrade complete for f9e08a169e03.")
    # ### end Modified Alembic commands ###