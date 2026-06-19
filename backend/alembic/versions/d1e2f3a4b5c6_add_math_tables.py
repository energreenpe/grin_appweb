"""add_math_tables

Crea las tablas del módulo MATH: calculos, equipos_tecnicos, regiones y
electrodomesticos_catalogo. Sin FK a quote/inspector (solo a datos_cliente y
usuarios, de shared).

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a7
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── equipos_tecnicos ──────────────────────────────────────────────
    op.create_table(
        'equipos_tecnicos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=40), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=False),
        sa.Column('marca', sa.String(length=120), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('specs', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_equipos_tecnicos_id'), 'equipos_tecnicos', ['id'], unique=False)
    op.create_index(op.f('ix_equipos_tecnicos_tipo'), 'equipos_tecnicos', ['tipo'], unique=False)
    op.create_index('ix_equipos_tecnicos_tipo_activo', 'equipos_tecnicos', ['tipo', 'activo'], unique=False)

    # ── regiones ──────────────────────────────────────────────────────
    op.create_table(
        'regiones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('hsp_minimo', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('hsp_promedio', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('hsp_mayor', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_regiones_id'), 'regiones', ['id'], unique=False)
    op.create_index(op.f('ix_regiones_nombre'), 'regiones', ['nombre'], unique=True)

    # ── electrodomesticos_catalogo ────────────────────────────────────
    op.create_table(
        'electrodomesticos_catalogo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('potencia_w', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('categoria', sa.String(length=80), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_electrodomesticos_catalogo_id'), 'electrodomesticos_catalogo', ['id'], unique=False)
    op.create_index(op.f('ix_electrodomesticos_catalogo_nombre'), 'electrodomesticos_catalogo', ['nombre'], unique=True)

    # ── calculos ──────────────────────────────────────────────────────
    op.create_table(
        'calculos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre_proyecto', sa.String(length=255), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('tipo_cliente', sa.String(length=50), nullable=False),
        sa.Column('ingeniero_id', sa.Integer(), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('tipo_sistema', sa.String(length=100), nullable=True),
        sa.Column('entrada', sa.JSON(), nullable=False),
        sa.Column('resultado', sa.JSON(), nullable=True),
        sa.Column('estado', sa.String(length=30), nullable=False, server_default='borrador'),
        sa.Column('paso_actual', sa.String(length=50), nullable=True, server_default='inicio'),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('fecha', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['datos_cliente.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['ingeniero_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_calculos_id'), 'calculos', ['id'], unique=False)
    op.create_index(op.f('ix_calculos_cliente_id'), 'calculos', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_calculos_ingeniero_id'), 'calculos', ['ingeniero_id'], unique=False)
    op.create_index(op.f('ix_calculos_fecha'), 'calculos', ['fecha'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_calculos_fecha'), table_name='calculos')
    op.drop_index(op.f('ix_calculos_ingeniero_id'), table_name='calculos')
    op.drop_index(op.f('ix_calculos_cliente_id'), table_name='calculos')
    op.drop_index(op.f('ix_calculos_id'), table_name='calculos')
    op.drop_table('calculos')

    op.drop_index(op.f('ix_electrodomesticos_catalogo_nombre'), table_name='electrodomesticos_catalogo')
    op.drop_index(op.f('ix_electrodomesticos_catalogo_id'), table_name='electrodomesticos_catalogo')
    op.drop_table('electrodomesticos_catalogo')

    op.drop_index(op.f('ix_regiones_nombre'), table_name='regiones')
    op.drop_index(op.f('ix_regiones_id'), table_name='regiones')
    op.drop_table('regiones')

    op.drop_index('ix_equipos_tecnicos_tipo_activo', table_name='equipos_tecnicos')
    op.drop_index(op.f('ix_equipos_tecnicos_tipo'), table_name='equipos_tecnicos')
    op.drop_index(op.f('ix_equipos_tecnicos_id'), table_name='equipos_tecnicos')
    op.drop_table('equipos_tecnicos')
