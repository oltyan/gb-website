"""home background url

Revision ID: a3f2b1c84e07
Revises: ccea996c05f3
Create Date: 2026-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f2b1c84e07'
down_revision = 'ccea996c05f3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.add_column(
            sa.Column(
                'home_background_url',
                sa.String(length=1024),
                nullable=False,
                server_default='',
            )
        )


def downgrade():
    with op.batch_alter_table('site_settings') as batch_op:
        batch_op.drop_column('home_background_url')
