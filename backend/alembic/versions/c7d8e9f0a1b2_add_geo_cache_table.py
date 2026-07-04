"""add_geo_cache_table

Revision ID: c7d8e9f0a1b2
Revises: fb59ae7fba2b
Create Date: 2026-06-17 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'fb59ae7fba2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'geo_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lat_key', sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column('lng_key', sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column('direccion', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lat_key', 'lng_key', name='uq_geo_cache_grid'),
    )
    op.create_index(op.f('ix_geo_cache_id'), 'geo_cache', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_geo_cache_id'), table_name='geo_cache')
    op.drop_table('geo_cache')
