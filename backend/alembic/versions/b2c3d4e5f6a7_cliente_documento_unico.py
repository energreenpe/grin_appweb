"""RUC/DNI único por cliente (índice parcial) + normalizar documentos vacíos

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-15

- Normaliza documento='' a NULL (un RUC/DNI vacío no debe emparejar clientes).
- Crea un índice ÚNICO PARCIAL sobre documento (solo cuando tiene valor), para
  impedir dos clientes con el mismo RUC/DNI. Los NULL no se consideran iguales.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE datos_cliente SET documento = NULL WHERE documento = ''")
    op.create_index(
        'uq_datos_cliente_documento',
        'datos_cliente',
        ['documento'],
        unique=True,
        postgresql_where=sa.text('documento IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_datos_cliente_documento', table_name='datos_cliente')
