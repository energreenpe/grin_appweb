"""add_list_plantillas_table

Crea la tabla del módulo LIST: list_plantillas (configuraciones reutilizables de
campos/overlays en PDF points). Reemplaza las plantillas que LIST guardaba como
archivos JSON en disco. Sin FK a otros módulos.

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-06-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'list_plantillas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('pdf_name', sa.String(length=255), nullable=False),
        sa.Column('fields', sa.JSON(), nullable=False),
        sa.Column('overlays', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_list_plantillas_id'), 'list_plantillas', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_list_plantillas_id'), table_name='list_plantillas')
    op.drop_table('list_plantillas')
