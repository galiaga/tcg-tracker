"""Add ON DELETE CASCADE to matches_user_deck_id_fkey

Revision ID: 0c275bc47412
Revises: beae9c0631ce
Create Date: 2025-04-16 16:30:41.237167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c275bc47412'
down_revision = 'beae9c0631ce'
branch_labels = None
depends_on = None

def upgrade():
    print("Applying ON DELETE CASCADE to user_decks_deck_id_fkey (Manual Migration)")
    with op.batch_alter_table('user_decks', schema=None) as batch_op:
        # Drop the existing constraint first
        batch_op.drop_constraint('user_decks_deck_id_fkey', type_='foreignkey')
        # Recreate the constraint with ON DELETE CASCADE
        batch_op.create_foreign_key(
            'user_decks_deck_id_fkey', # Constraint name
            'decks',                   # Referenced table
            ['deck_id'],               # Local column(s)
            ['id'],                    # Remote column(s)
            ondelete='CASCADE'         # Add the cascade rule!
        )
    print("Ensured constraint 'user_decks_deck_id_fkey' exists with ON DELETE CASCADE")


def downgrade():
    print("Removing ON DELETE CASCADE from user_decks_deck_id_fkey (Manual Migration)")
    with op.batch_alter_table('user_decks', schema=None) as batch_op:
        # Drop the cascade constraint
        batch_op.drop_constraint('user_decks_deck_id_fkey', type_='foreignkey')
        # Recreate the original constraint without ON DELETE CASCADE
        batch_op.create_foreign_key(
            'user_decks_deck_id_fkey', # Constraint name
            'decks',                   # Referenced table
            ['deck_id'],               # Local column(s)
            ['id']                     # Remote column(s)
            # No ondelete='CASCADE' here
        )
    print("Reverted constraint 'user_decks_deck_id_fkey' to no action on delete")