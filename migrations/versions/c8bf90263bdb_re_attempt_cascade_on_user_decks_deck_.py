# migrations/versions/c8bf90263bdb_re_attempt_cascade_on_user_decks_deck_.py

"""Re-attempt cascade on user_decks_deck_id_fkey directly (using batch mode, new name, no explicit drop)

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

# Define names clearly
original_constraint_name = 'user_decks_deck_id_fkey'
# Use a distinct name for the new constraint with cascade
new_constraint_name = 'user_decks_deck_id_fkey_cascade'
table_name = 'user_decks'
referenced_table = 'decks'
local_cols = ['deck_id']
remote_cols = ['id']

def upgrade():
    print(f"Attempting BATCH create for constraint on {table_name} (using new name: {new_constraint_name})")
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        # --- REMOVED THE DROP CONSTRAINT CALL ---
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
            ondelete='CASCADE'
        )
        print(f"Successfully created constraint {new_constraint_name} with CASCADE")

def downgrade():
    # Downgrade remains the same as the previous attempt: drop the new, recreate the old.
    print(f"Reverting constraint on {table_name} (removing CASCADE) using BATCH mode")
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