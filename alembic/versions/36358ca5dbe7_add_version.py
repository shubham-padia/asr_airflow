"""add_version

Revision ID: 36358ca5dbe7
Revises: 48a1378f9dda
Create Date: 2019-04-11 15:10:15.112026

"""
from alembic import op
from sqlalchemy import Column, String
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36358ca5dbe7'
down_revision = '48a1378f9dda'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('metadata_registry',
            Column('version', String())
            )


def downgrade():
    op.drop_column('metadata_registry', 'version')
