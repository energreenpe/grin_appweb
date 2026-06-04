"""Initial QUOTE tables

Revision ID: 001
Revises:
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── productos ────────────────────────────────────────────────────────────
    op.create_table(
        "productos",
        sa.Column("id",          sa.Integer(),      nullable=False),
        sa.Column("categoria",   sa.String(100),    nullable=False),
        sa.Column("nombre",      sa.String(255),    nullable=False),
        sa.Column("descripcion", sa.Text(),         nullable=True),
        sa.Column("marca",       sa.String(100),    nullable=True),
        sa.Column("unidad",      sa.String(50),     nullable=False, server_default="und"),
        sa.Column("precio",      sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("moneda",      sa.String(3),      nullable=False, server_default="PEN"),
        sa.Column("activo",      sa.Boolean(),      nullable=False, server_default="true"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_productos_categoria", "productos", ["categoria"])
    op.create_index("idx_productos_nombre",    "productos", ["nombre"])

    # ── usuarios ─────────────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id",         sa.Integer(),     nullable=False),
        sa.Column("nombre",     sa.String(255),   nullable=False),
        sa.Column("correo",     sa.String(100),   nullable=False),
        sa.Column("telefono",   sa.String(30),    nullable=True),
        sa.Column("activo",     sa.Boolean(),     nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("correo"),
    )
    op.create_index("idx_usuarios_correo", "usuarios", ["correo"])

    # ── empresa_config ───────────────────────────────────────────────────────
    op.create_table(
        "empresa_config",
        sa.Column("id",         sa.Integer(),    nullable=False, server_default="1"),
        sa.Column("nombre",     sa.String(255),  nullable=False, server_default="Energreen Perú E.I.R.L."),
        sa.Column("ruc",        sa.String(11),   nullable=True,  server_default="20604756821"),
        sa.Column("direccion",  sa.Text(),        nullable=True,  server_default="Urb. Los Tallanes 1ra Etapa Mz. C-16, Piura"),
        sa.Column("telefono",   sa.String(20),   nullable=True),
        sa.Column("email",      sa.String(100),  nullable=True),
        sa.Column("logo_path",  sa.String(255),  nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 1", name="solo_una_fila"),
    )
    # Insertar fila única inicial
    op.execute(
        "INSERT INTO empresa_config (id, nombre, ruc, direccion) "
        "VALUES (1, 'Energreen Perú E.I.R.L.', '20604756821', "
        "'Urb. Los Tallanes 1ra Etapa Mz. C-16, Piura, Piura, Piura') "
        "ON CONFLICT (id) DO NOTHING"
    )

    # ── cotizaciones ─────────────────────────────────────────────────────────
    op.create_table(
        "cotizaciones",
        sa.Column("id",                     sa.Integer(),      nullable=False),
        sa.Column("correlativo",            sa.String(20),     nullable=False),
        sa.Column("vendedor_nombre",        sa.String(255),    nullable=True),
        sa.Column("vendedor_correo",        sa.String(100),    nullable=True),
        sa.Column("vendedor_tel",           sa.String(30),     nullable=True),
        sa.Column("version",                sa.String(10),     server_default="1.0"),
        sa.Column("cliente_nombre",         sa.String(255),    nullable=False),
        sa.Column("cliente_doc",            sa.String(15),     nullable=True),
        sa.Column("tipo_doc",               sa.String(5),      server_default="RUC"),
        sa.Column("cliente_dir",            sa.Text(),          nullable=True),
        sa.Column("cliente_atencion",       sa.String(255),    nullable=True),
        sa.Column("cliente_referencia",     sa.String(255),    nullable=True),
        sa.Column("cliente_correo",         sa.String(100),    nullable=True),
        sa.Column("cliente_tel",            sa.String(30),     nullable=True),
        sa.Column("moneda",                 sa.String(20),     nullable=False, server_default="Soles (PEN)"),
        sa.Column("tipo_cambio",            sa.Numeric(8, 4),  nullable=False, server_default="3.80"),
        sa.Column("utilidad",               sa.Numeric(6, 4),  nullable=False, server_default="1.30"),
        sa.Column("mostrar_precios",        sa.Boolean(),      nullable=False, server_default="true"),
        sa.Column("cond_tecnicas",          postgresql.JSON(), server_default="[]"),
        sa.Column("cond_comerciales",       postgresql.JSON(), server_default="[]"),
        sa.Column("cond_otras",             postgresql.JSON(), server_default="[]"),
        sa.Column("cond_garantia",          postgresql.JSON(), server_default="[]"),
        sa.Column("cond_garantia_servicio", sa.Text(),          server_default=""),
        sa.Column("cuentas_bancarias",      postgresql.JSON(), server_default="[]"),
        sa.Column("estado",                 sa.String(20),     nullable=False, server_default="borrador"),
        sa.Column("notas",                  sa.Text(),          nullable=True),
        sa.Column("created_at",             sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",             sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("correlativo"),
    )
    op.create_index("idx_cotizaciones_estado",      "cotizaciones", ["estado"])
    op.create_index("idx_cotizaciones_correlativo", "cotizaciones", ["correlativo"])

    # ── items_cotizacion ─────────────────────────────────────────────────────
    op.create_table(
        "items_cotizacion",
        sa.Column("id",            sa.Integer(),      nullable=False),
        sa.Column("cotizacion_id", sa.Integer(),      nullable=False),
        sa.Column("producto_id",   sa.Integer(),      nullable=True),
        sa.Column("nombre",        sa.String(255),    nullable=False),
        sa.Column("descripcion",   sa.Text(),          nullable=True),
        sa.Column("marca",         sa.String(100),    nullable=True),
        sa.Column("unidad",        sa.String(50),     nullable=False, server_default="und"),
        sa.Column("cantidad",      sa.Numeric(10, 2), nullable=False, server_default="1"),
        sa.Column("precio_unit",   sa.Numeric(12, 2), nullable=False),
        sa.Column("moneda",        sa.String(3),      nullable=False, server_default="PEN"),
        sa.Column("particion",     sa.String(100),    nullable=False, server_default="Principal"),
        sa.Column("subparticion",  sa.String(100),    nullable=True),
        sa.Column("orden",         sa.Integer(),      nullable=False, server_default="0"),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cotizacion_id"], ["cotizaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"],   ["productos.id"],    ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_items_cotizacion_id", "items_cotizacion", ["cotizacion_id"])


def downgrade() -> None:
    op.drop_table("items_cotizacion")
    op.drop_table("cotizaciones")
    op.drop_table("empresa_config")
    op.drop_table("usuarios")
    op.drop_table("productos")
