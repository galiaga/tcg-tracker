# migrations/versions/5a3e126c5ace_add_cascade_to_match_tags_match_id_fkey_.py

"""Add cascade to match_tags_match_id_fkey (using batch mode, new name, no explicit drop)

Revision ID: 5a3e126c5ace
Revises: 0bb62b4f7c80
Create Date: 2025-04-17 12:21:14.227071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a3e126c5ace'
down_revision = '0bb62b4f7c80' # Correctly points to the previous migration
branch_labels = None
depends_on = None

# Define names and details clearly
original_constraint_name = 'match_tags_match_id_fkey'
# Use a distinct name for the new constraint with cascade
new_constraint_name = 'match_tags_match_id_fkey_cascade' # New name
table_name = 'match_tags'
referenced_table = 'matches'      # Table the constraint points to
local_cols = ['match_id']         # Column(s) in 'match_tags' table
remote_cols = ['id']              # Column(s) in 'matches' table

def upgrade():
    print(f"Attempting BATCH create for constraint on {table_name} (using new name: {new_constraint_name})")
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        # --- REMOVED THE EXPLICIT DROP CONSTRAINT CALL ---
        # print(f"Dropping original constraint: {original_constraint_name}...")
        # batch_op.drop_constraint(original_constraint_name, type_='foreignkey')
        # print(f"Successfully dropped constraint {original_constraint_name}")

        # Create the new constraint with ON DELETE CASCADE and the NEW NAME
        print(f"Creating new constraint: {new_constraint_name} with CASCADE...")
        batch_op.create_foreign_key(
            new_constraint_name,    # <<< Use the NEW constraint name here
            referenced_table,
            local_cols,
            remote_cols,
            ondelete='CASCADE'      # Add the cascade rule!
        )
        print(f"Successfully created constraint {new_constraint_name} with CASCADE")

def downgrade():
    print(f"Reverting constraint on {table_name} (removing CASCADE) using BATCH mode")
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        # Drop the cascade constraint (using the NEW NAME)
        print(f"Dropping constraint: {new_constraint_name}...")
        batch_op.drop_constraint(new_constraint_name, type_='foreignkey') # <<< Drop the NEW name
        print(f"Successfully dropped constraint {new_constraint_name}")

        # Recreate the original constraint (using the ORIGINAL NAME)
        print(f"Recreating original constraint: {original_constraint_name} without CASCADE...")
        batch_op.create_foreign_key(
            original_constraint_name, # <<< Recreate the ORIGINAL name
            referenced_table,
            local_cols,
            remote_cols
            # No ondelete='CASCADE' here
        )
        print(f"Successfully recreated constraint {original_constraint_name} without CASCADE")