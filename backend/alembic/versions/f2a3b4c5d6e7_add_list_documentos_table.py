"""add_list_documentos_table

Crea la tabla list_documentos: documentos subidos/convertidos en edición, persistidos
para reabrir y continuar (autoguardado de fields/overlays). Su PDF base es permanente.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'list_documentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('pdf_name', sa.String(length=255), nullable=False),
        sa.Column('fields', sa.JSON(), nullable=False),
        sa.Column('overlays', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_list_documentos_id'), 'list_documentos', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_list_documentos_id'), table_name='list_documentos')
    op.drop_table('list_documentos')
