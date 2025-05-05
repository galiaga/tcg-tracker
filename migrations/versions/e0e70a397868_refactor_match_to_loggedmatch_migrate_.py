# migrations/versions/e0e70a397868_refactor_match_to_loggedmatch_migrate_.py

"""Refactor Match to LoggedMatch, migrate data

Revision ID: e0e70a397868
Revises: 786fcb4a0387
Create Date: 2025-05-02 17:45:07.075739 # Keep original date

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e0e70a397868'
down_revision = '786fcb4a0387'
branch_labels = None
depends_on = None

# --- Define table names for clarity ---
OLD_TABLE_NAME = 'matches'
NEW_TABLE_NAME = 'logged_matches'
USER_DECKS_TABLE = 'user_decks'
USERS_TABLE = 'users'
DECKS_TABLE = 'decks'
TAGS_TABLE = 'tags'
MATCH_TAGS_TABLE = 'match_tags' # Association table

# --- Define NEW constraint names for clarity (Optional, Alembic can generate them) ---
NEW_FK_LOGGER_CONSTRAINT_NAME = f'fk_{NEW_TABLE_NAME}_logger_user_id_{USERS_TABLE}'
NEW_FK_DECK_CONSTRAINT_NAME = f'fk_{NEW_TABLE_NAME}_deck_id_{DECKS_TABLE}'
MATCH_TAGS_NEW_FK_NAME = f'fk_{MATCH_TAGS_TABLE}_match_id_{NEW_TABLE_NAME}'
CHECK_CONSTRAINT_NEW_NAME = 'check_logged_match_result' # New name from LoggedMatch model


def upgrade():
    print(f"--- Starting Upgrade: Refactor {OLD_TABLE_NAME} to {NEW_TABLE_NAME} ---")

    # 1. RENAME THE TABLE FIRST
    print(f"1. Renaming table {OLD_TABLE_NAME} to {NEW_TABLE_NAME}")
    op.rename_table(OLD_TABLE_NAME, NEW_TABLE_NAME)

    # --- Batch 1: Add Nullable Columns and Indexes ---
    print("--- Starting Batch 1: Add Nullable Columns & Indexes ---")
    with op.batch_alter_table(NEW_TABLE_NAME, schema=None) as batch_op:
        # 2. Add new columns (initially nullable)
        print("2. Adding new columns (nullable): logger_user_id, deck_id, opponent_description, match_format")
        batch_op.add_column(sa.Column('logger_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('deck_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('opponent_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('match_format', sa.String(length=50), nullable=True))

        # 3. Create indexes for new columns
        print("3. Creating indexes for new columns")
        batch_op.create_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_logger_user_id'), ['logger_user_id'], unique=False)
        batch_op.create_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_deck_id'), ['deck_id'], unique=False)
        batch_op.create_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_timestamp'), ['timestamp'], unique=False)
    print("--- Finished Batch 1 ---")

    # --- Step 4: Data Migration (Outside Batch) ---
    print(f"4. Populating logger_user_id and deck_id from {USER_DECKS_TABLE} via user_deck_id...")
    populate_sql = f"""
        UPDATE {NEW_TABLE_NAME}
        SET logger_user_id = (SELECT user_id FROM {USER_DECKS_TABLE} WHERE {USER_DECKS_TABLE}.id = {NEW_TABLE_NAME}.user_deck_id),
            deck_id = (SELECT deck_id FROM {USER_DECKS_TABLE} WHERE {USER_DECKS_TABLE}.id = {NEW_TABLE_NAME}.user_deck_id)
        WHERE {NEW_TABLE_NAME}.user_deck_id IS NOT NULL;
    """
    op.execute(populate_sql)
    print("   Data population SQL executed.")
    # --- END DATA MIGRATION ---

    # --- Batch 2: Make Columns Non-Nullable, Add FKs, Drop Old Column ---
    print("--- Starting Batch 2: Finalize Columns & Constraints ---")
    with op.batch_alter_table(NEW_TABLE_NAME, schema=None) as batch_op:
        # 5. Make new columns non-nullable
        print("5. Making logger_user_id and deck_id non-nullable")
        batch_op.alter_column('logger_user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('deck_id', existing_type=sa.Integer(), nullable=False)

        # 6. Create new foreign key constraints
        print("6. Creating new foreign key constraints")
        batch_op.create_foreign_key(
            NEW_FK_LOGGER_CONSTRAINT_NAME, USERS_TABLE,
            ['logger_user_id'], ['id'])
        batch_op.create_foreign_key(
            NEW_FK_DECK_CONSTRAINT_NAME, DECKS_TABLE,
            ['deck_id'], ['id'])

        # 7. Drop the old user_deck_id column (and its implicit FK)
        print("8. Dropping old column: user_deck_id (FK handled implicitly by batch mode)")
        batch_op.drop_column('user_deck_id')

        # 8. Check constraint handling (Skipped for SQLite)
        print(f"9. Skipping check constraint rename (SQLite limitation). Original check should persist.")
    print("--- Finished Batch 2 ---")


    # --- Batch 3: Update match_tags association table ---
    print(f"--- Starting Batch 3: Update {MATCH_TAGS_TABLE} FK ---")
    with op.batch_alter_table(MATCH_TAGS_TABLE, schema=None) as batch_op:
        # 10. Update the match_tags foreign key
        print(f"10. Updating foreign key in {MATCH_TAGS_TABLE} to point to {NEW_TABLE_NAME}.id")

        # --- MODIFIED SECTION ---
        # REMOVED the explicit batch_op.drop_constraint call entirely.
        # We rely on the batch process potentially not carrying over the old unnamed FK,
        # and then we explicitly create the new one we want.
        print(f"    Skipping explicit drop of old FK constraint on {MATCH_TAGS_TABLE}. Relying on batch process and explicit create.")
        # --- END MODIFIED SECTION ---

        # Create the new FK constraint we definitely want
        print(f"    Creating new FK constraint: {MATCH_TAGS_NEW_FK_NAME}")
        batch_op.create_foreign_key(
            MATCH_TAGS_NEW_FK_NAME, NEW_TABLE_NAME, # Point to the NEW table name
            ['match_id'], ['id'], # Local column -> Referenced column
            ondelete='CASCADE' # Re-apply ondelete if needed
        )
    print("--- Finished Batch 3 ---")

    print(f"--- Upgrade Complete: {OLD_TABLE_NAME} refactored to {NEW_TABLE_NAME} ---")


# Keep the downgrade function as it was in the previous version
def downgrade():
    # Downgrade remains complex - restoring from backup is safer.
    print("--- Starting Downgrade (Complex, Restore Recommended) ---")

    # 1. Update match_tags FK back to 'matches'
    print(f"1. Updating foreign key in {MATCH_TAGS_TABLE} back to {OLD_TABLE_NAME}.id")
    with op.batch_alter_table(MATCH_TAGS_TABLE, schema=None) as batch_op:
        try:
            # Drop the new constraint using its generated name
            batch_op.drop_constraint(MATCH_TAGS_NEW_FK_NAME, type_='foreignkey')
            print(f"    Dropped new constraint {MATCH_TAGS_NEW_FK_NAME}")
        except Exception as e:
            print(f"   WARNING: Could not drop constraint '{MATCH_TAGS_NEW_FK_NAME}'. Error: {e}")

        # Recreate the old constraint implicitly (best effort for SQLite)
        print(f"    Attempting to recreate old FK constraint on {MATCH_TAGS_TABLE} implicitly...")
        try:
            # Create unnamed constraint
            batch_op.create_foreign_key(None, OLD_TABLE_NAME, ['match_id'], ['id'], ondelete='CASCADE')
            print("    Recreated old constraint implicitly.")
        except Exception as e_unnamed_create:
            print(f"   WARNING: Could not create unnamed {MATCH_TAGS_TABLE} FK constraint. Error: {e_unnamed_create}")


    # 2. Reverse operations on the main table (now named logged_matches)
    with op.batch_alter_table(NEW_TABLE_NAME, schema=None) as batch_op:
        # Add back user_deck_id (nullable first)
        print("2. Adding back user_deck_id column (nullable)")
        batch_op.add_column(sa.Column('user_deck_id', sa.Integer(), nullable=True))

        # --- DATA MIGRATION (Reverse - Best Effort) ---
        print("3. Attempting to populate user_deck_id (BEST EFFORT - MAY BE INACCURATE)")
        populate_reverse_sql = f"""
            UPDATE {NEW_TABLE_NAME}
            SET user_deck_id = (
                SELECT id FROM {USER_DECKS_TABLE}
                WHERE {USER_DECKS_TABLE}.user_id = {NEW_TABLE_NAME}.logger_user_id
                  AND {USER_DECKS_TABLE}.deck_id = {NEW_TABLE_NAME}.deck_id
                LIMIT 1
            )
            WHERE {NEW_TABLE_NAME}.logger_user_id IS NOT NULL AND {NEW_TABLE_NAME}.deck_id IS NOT NULL;
        """
        # Note: Execute outside batch if needed, but might be okay here for downgrade
        op.execute(populate_reverse_sql)
        try:
             batch_op.alter_column('user_deck_id', existing_type=sa.Integer(), nullable=False)
             print("   Made user_deck_id non-nullable.")
        except Exception as e:
             print(f"   WARNING: Could not make user_deck_id non-nullable. Some rows might be NULL. Error: {e}")
        # --- END REVERSE DATA MIGRATION ---

        # Drop new FKs
        print("4. Dropping new foreign key constraints")
        try: batch_op.drop_constraint(NEW_FK_LOGGER_CONSTRAINT_NAME, type_='foreignkey')
        except Exception as e: print(f"   Warning dropping {NEW_FK_LOGGER_CONSTRAINT_NAME}: {e}")
        try: batch_op.drop_constraint(NEW_FK_DECK_CONSTRAINT_NAME, type_='foreignkey')
        except Exception as e: print(f"   Warning dropping {NEW_FK_DECK_CONSTRAINT_NAME}: {e}")

        # Add old FK back implicitly
        print(f"5. Attempting to recreate old user_deck_id FK constraint implicitly...")
        try:
            batch_op.create_foreign_key(None, USER_DECKS_TABLE, ['user_deck_id'], ['id'])
            print("   Recreated old constraint implicitly.")
        except Exception as e_unnamed_create_ud:
            print(f"   WARNING: Could not create unnamed user_deck_id FK constraint. Error: {e_unnamed_create_ud}")


        # Drop new columns and their indexes
        print("6. Dropping new columns: logger_user_id, deck_id, opponent_description, match_format and indexes")
        try: batch_op.drop_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_timestamp'))
        except Exception as e: print(f"   Warning dropping ix_{NEW_TABLE_NAME}_timestamp: {e}")
        try: batch_op.drop_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_logger_user_id'))
        except Exception as e: print(f"   Warning dropping ix_{NEW_TABLE_NAME}_logger_user_id: {e}")
        try: batch_op.drop_index(batch_op.f(f'ix_{NEW_TABLE_NAME}_deck_id'))
        except Exception as e: print(f"   Warning dropping ix_{NEW_TABLE_NAME}_deck_id: {e}")

        batch_op.drop_column('match_format')
        batch_op.drop_column('opponent_description')
        batch_op.drop_column('deck_id')
        batch_op.drop_column('logger_user_id')

        # 7. Check constraint handling (SQLite limitations)
        print("7. Skipping check constraint restoration (SQLite limitation).")


    # Rename table back LAST
    print(f"8. Renaming table {NEW_TABLE_NAME} back to {OLD_TABLE_NAME}")
    op.rename_table(NEW_TABLE_NAME, OLD_TABLE_NAME)

    print("--- Downgrade Attempt Complete (Data Loss Possible) ---")