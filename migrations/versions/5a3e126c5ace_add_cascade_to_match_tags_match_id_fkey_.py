"""Add cascade to match_tags_match_id_fkey directly

Revision ID: 5a3e126c5ace
Revises: 0bb62b4f7c80
Create Date: 2025-04-17 12:21:14.227071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a3e126c5ace'
down_revision = '0bb62b4f7c80'
branch_labels = None
depends_on = None

# <<< CHANGE THESE DETAILS >>>
constraint_name = 'match_tags_match_id_fkey' # Constraint to modify
table_name = 'match_tags'                    # Table containing the constraint
referenced_table = 'matches'                 # Table the constraint points to
local_cols = ['match_id']                    # Column(s) in 'match_tags' table
remote_cols = ['id']                         # Column(s) in 'matches' table
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