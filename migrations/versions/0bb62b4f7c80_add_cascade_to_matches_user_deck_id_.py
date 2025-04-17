"""Add cascade to matches_user_deck_id_fkey directly

Revision ID: 0bb62b4f7c80
Revises: c8bf90263bdb
Create Date: 2025-04-17 12:15:04.031304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bb62b4f7c80'
down_revision = 'c8bf90263bdb'
branch_labels = None
depends_on = None

# <<< CHANGE THESE DETAILS >>>
constraint_name = 'matches_user_deck_id_fkey' # Constraint to modify
table_name = 'matches'                        # Table containing the constraint
referenced_table = 'user_decks'               # Table the constraint points to
local_cols = ['user_deck_id']                 # Column(s) in 'matches' table
remote_cols = ['id']                          # Column(s) in 'user_decks' table
# <<< END CHANGES >>>

def upgrade():
    print(f"Attempting DIRECT drop/create for constraint {constraint_name} on {table_name}")
    try:
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        print(f"Successfully dropped constraint {constraint_name}")
    except Exception as e:
        print(f"WARNING: Could not drop constraint {constraint_name} (maybe it didn't exist?): {e}")

    try:
        op.create_foreign_key(
            constraint_name,
            table_name,
            referenced_table,
            local_cols,
            remote_cols,
            ondelete='CASCADE'  # Add the cascade rule!
        )
        print(f"Successfully created constraint {constraint_name} with ON DELETE CASCADE")
    except Exception as e:
        print(f"ERROR: Failed to create constraint {constraint_name} with CASCADE: {e}")
        raise e

def downgrade():
    print(f"Reverting constraint {constraint_name} on {table_name} (removing CASCADE)")
    try:
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        print(f"Successfully dropped constraint {constraint_name}")
    except Exception as e:
        print(f"WARNING: Could not drop constraint {constraint_name} during downgrade: {e}")

    try:
        op.create_foreign_key(
            constraint_name,
            table_name,
            referenced_table,
            local_cols,
            remote_cols
            # No ondelete='CASCADE' here
        )
        print(f"Successfully recreated constraint {constraint_name} without CASCADE")
    except Exception as e:
        print(f"ERROR: Failed to recreate constraint {constraint_name} without CASCADE: {e}")
        raise e