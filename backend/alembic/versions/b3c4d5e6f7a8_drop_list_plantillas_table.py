"""drop_list_plantillas_table

Elimina la tabla list_plantillas y su funcionalidad de guardar/cargar plantilla
del módulo LIST: cada documento tiene un formato de campos único, así que
reutilizar una distribución de campos entre documentos no aporta valor en este
módulo (a diferencia de las plantillas de QUOTE, que no se tocan).

Revision ID: b3c4d5e6f7a8
Revises: a60b4e4b2c89
Create Date: 2026-07-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a60b4e4b2c89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_list_plantillas_id'), table_name='list_plantillas')
    op.drop_table('list_plantillas')


def downgrade() -> None:
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
