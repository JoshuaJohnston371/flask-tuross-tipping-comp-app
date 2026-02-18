"""add chat round number

Revision ID: 7b2f4c8d1a9e
Revises: 4ecaeb8a4a34
Create Date: 2026-02-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b2f4c8d1a9e'
down_revision = '4ecaeb8a4a34'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_messages', sa.Column('round_number', sa.Integer(), nullable=True))
    op.alter_column('chat_messages', 'match_id', existing_type=sa.String(), nullable=True)
    op.execute(
        """
        UPDATE chat_messages
        SET round_number = ff.round
        FROM fixture_free ff
        WHERE chat_messages.match_id = ff.match_id
          AND chat_messages.round_number IS NULL;
        """
    )


def downgrade():
    op.alter_column('chat_messages', 'match_id', existing_type=sa.String(), nullable=False)
    op.drop_column('chat_messages', 'round_number')
