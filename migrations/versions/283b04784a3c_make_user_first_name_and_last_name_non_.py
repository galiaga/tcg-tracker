"""Make user first_name and last_name non-nullable

Revision ID: 283b04784a3c
Revises: 16534a6265c0
Create Date: 2025-04-29 17:02:34.449394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '283b04784a3c'
down_revision = '16534a6265c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)

    # ### end Alembic commands ###
