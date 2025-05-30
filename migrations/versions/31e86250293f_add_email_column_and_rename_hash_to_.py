"""Add email column and rename hash to password_hash in User model

Revision ID: 31e86250293f
Revises: 966603d38ad7
Create Date: 2025-04-28 11:46:28.452656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31e86250293f'
down_revision = '966603d38ad7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        # 1. Add the new email column (as nullable=True, which is correct)
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))

        # 2. Rename 'hash' to 'password_hash'.
        #    Ensure existing_type matches the OLD 'hash' column definition.
        #    Keep nullable=False as per the new model definition.
        #    This tells Alembic to copy data from 'hash' to 'password_hash'.
        batch_op.alter_column('hash',
                              new_column_name='password_hash',
                              existing_type=sa.String(length=255), # Adjust length if your old hash was different
                              nullable=False)

        # 3. Create the index for email AFTER adding the column.
        #    The unique constraint is handled by the column definition itself.
        batch_op.create_index('ix_users_email', ['email'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hash', sa.VARCHAR(length=255), nullable=False))
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.drop_column('password_hash')
        batch_op.drop_column('email')

    # ### end Alembic commands ###
