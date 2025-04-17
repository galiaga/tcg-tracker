"""Re-attempt cascade on user_decks_deck_id_fkey directly

Revision ID: c8bf90263bdb
Revises: 4787278ff358
Create Date: 2025-04-17 12:02:11.803234

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8bf90263bdb'
down_revision = '4787278ff358'
branch_labels = None
depends_on = None

constraint_name = 'user_decks_deck_id_fkey'
table_name = 'user_decks'
referenced_table = 'decks'
local_cols = ['deck_id']
remote_cols = ['id']

def upgrade():
    print(f"Attempting DIRECT drop/create for constraint {constraint_name} on {table_name}")
    try:
        # Drop the existing constraint
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        print(f"Successfully dropped constraint {constraint_name}")
    except Exception as e:
        # Log error, but proceed. Maybe it was already gone? Unlikely given \d output.
        print(f"WARNING: Could not drop constraint {constraint_name} (maybe it didn't exist?): {e}")

    try:
        # Recreate the constraint with ON DELETE CASCADE
        op.create_foreign_key(
            constraint_name,      # Constraint name
            table_name,           # Source table
            referenced_table,     # Referenced table
            local_cols,           # Local column(s)
            remote_cols,          # Remote column(s)
            ondelete='CASCADE'    # Add the cascade rule!
        )
        print(f"Successfully created constraint {constraint_name} with ON DELETE CASCADE")
    except Exception as e:
        print(f"ERROR: Failed to create constraint {constraint_name} with CASCADE: {e}")
        # Re-raise to ensure the migration fails if creation doesn't work
        raise e

def downgrade():
    print(f"Reverting constraint {constraint_name} on {table_name} (removing CASCADE)")
    try:
        # Drop the cascade constraint
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        print(f"Successfully dropped constraint {constraint_name}")
    except Exception as e:
        print(f"WARNING: Could not drop constraint {constraint_name} during downgrade: {e}")

    try:
        # Recreate the original constraint without ON DELETE CASCADE
        op.create_foreign_key(
            constraint_name,      # Constraint name
            table_name,           # Source table
            referenced_table,     # Referenced table
            local_cols,           # Local column(s)
            remote_cols           # Remote column(s)
            # No ondelete='CASCADE' here
        )
        print(f"Successfully recreated constraint {constraint_name} without CASCADE")
    except Exception as e:
        print(f"ERROR: Failed to recreate constraint {constraint_name} without CASCADE: {e}")
        raise e