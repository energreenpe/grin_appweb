"""make tipo_sistema nullable in visitas

Revision ID: a60b4e4b2c89
Revises: c7d8e9f0a1b2
Create Date: 2026-07-06 20:04:48.577158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a60b4e4b2c89'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # El modelo (app/modules/inspector/models.py) declara tipo_sistema como
    # opcional desde antes (se elige en un paso posterior del wizard, no al
    # crear la visita) pero la migración original la creó NOT NULL. Este
    # desfase hacía que CUALQUIER creación de visita fallara con un
    # IntegrityError genérico ("Cliente o técnico inválido") al no enviar
    # tipo_sistema en el paso inicial del wizard.
    op.alter_column("visitas", "tipo_sistema", existing_type=sa.String(length=100), nullable=True)


def downgrade() -> None:
    op.alter_column("visitas", "tipo_sistema", existing_type=sa.String(length=100), nullable=False)
