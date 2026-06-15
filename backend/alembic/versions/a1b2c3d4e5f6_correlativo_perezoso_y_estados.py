"""Correlativo perezoso (CO{AA}-{NNNN}-version) + contador anual + limpieza

Revision ID: a1b2c3d4e5f6
Revises: fa42aec2415c
Create Date: 2026-06-13

- Borra las cotizaciones de prueba (formato viejo COT-YYYY-xxxx).
- Reemplaza la columna 'correlativo' (string único) por 'correlativo_anio' +
  'correlativo_num' (asignados al salir de borrador), con UNIQUE(anio, num).
- Crea la tabla 'correlativo_contador' (anio -> ultimo_numero) que solo avanza.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fa42aec2415c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Limpiar datos de prueba (los ítems caen por el ON DELETE CASCADE).
    op.execute("DELETE FROM items_cotizacion")
    op.execute("DELETE FROM cotizaciones")

    # 2) Quitar la columna vieja de correlativo (string único).
    op.drop_column('cotizaciones', 'correlativo')

    # 3) Agregar el número fijo (año + secuencial), nullable para borradores.
    op.add_column('cotizaciones', sa.Column('correlativo_anio', sa.Integer(), nullable=True))
    op.add_column('cotizaciones', sa.Column('correlativo_num', sa.Integer(), nullable=True))
    op.create_unique_constraint(
        'uq_cotizaciones_correlativo_anio_num',
        'cotizaciones',
        ['correlativo_anio', 'correlativo_num'],
    )

    # 4) Cambiar el default de version a 'A1'.
    op.alter_column('cotizaciones', 'version', server_default='A1',
                    existing_type=sa.String(length=10), existing_nullable=True)

    # 5) Tabla contador anual (solo avanza).
    op.create_table(
        'correlativo_contador',
        sa.Column('anio', sa.Integer(), primary_key=True),
        sa.Column('ultimo_numero', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('correlativo_contador')
    op.alter_column('cotizaciones', 'version', server_default='1.0',
                    existing_type=sa.String(length=10), existing_nullable=True)
    op.drop_constraint('uq_cotizaciones_correlativo_anio_num', 'cotizaciones', type_='unique')
    op.drop_column('cotizaciones', 'correlativo_num')
    op.drop_column('cotizaciones', 'correlativo_anio')
    op.add_column('cotizaciones', sa.Column('correlativo', sa.String(length=20), nullable=True))
    op.create_unique_constraint('cotizaciones_correlativo_key', 'cotizaciones', ['correlativo'])
