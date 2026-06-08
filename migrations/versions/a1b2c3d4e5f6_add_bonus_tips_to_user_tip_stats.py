"""add bonus tips to user tip stats

Revision ID: a1b2c3d4e5f6
Revises: 7b2f4c8d1a9e
Create Date: 2026-06-08 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7b2f4c8d1a9e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user_tip_stats', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bonus_tips', sa.Integer(), nullable=True))

    op.execute("UPDATE user_tip_stats SET bonus_tips = 0 WHERE bonus_tips IS NULL")

    with op.batch_alter_table('user_tip_stats', schema=None) as batch_op:
        batch_op.alter_column('bonus_tips', nullable=False, server_default='0')


def downgrade():
    with op.batch_alter_table('user_tip_stats', schema=None) as batch_op:
        batch_op.drop_column('bonus_tips')
