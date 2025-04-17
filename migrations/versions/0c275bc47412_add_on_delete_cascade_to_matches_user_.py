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
    print("Applying ON DELETE CASCADE to matches_user_deck_id_fkey (Manual Migration)")
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'matches_user_deck_id_fkey',  # Constraint name to create/ensure
            'user_decks',                 # Target table
            ['user_deck_id'],             # Local columns
            ['id'],                       # Remote columns
            ondelete='CASCADE'            # Add the cascade behavior
        )
        print("Ensured constraint 'matches_user_deck_id_fkey' exists with ON DELETE CASCADE")


def downgrade():
    print("Removing ON DELETE CASCADE from matches_user_deck_id_fkey (Manual Migration)")
    with op.batch_alter_table('matches', schema=None) as batch_op:
        # --- REMOVE or COMMENT OUT the drop constraint line ---
        # try:
        #     batch_op.drop_constraint('matches_user_deck_id_fkey', type_='foreignkey')
        #     print("Dropped constraint with CASCADE: matches_user_deck_id_fkey")
        # except Exception as e:
        #      print(f"Could not drop constraint 'matches_user_deck_id_fkey' during downgrade (may not exist): {e}")

        # Keep the create_foreign_key WITHOUT ON DELETE CASCADE
        batch_op.create_foreign_key(
            'matches_user_deck_id_fkey', # Constraint name to create/ensure
            'user_decks',                # Target table
            ['user_deck_id'],            # Local columns
            ['id']                       # Remote columns
            # No ondelete='CASCADE' here
        )
        print("Ensured constraint 'matches_user_deck_id_fkey' exists without CASCADE")