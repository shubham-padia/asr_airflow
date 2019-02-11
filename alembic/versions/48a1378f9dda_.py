"""empty message

Revision ID: 48a1378f9dda
Revises: 
Create Date: 2019-02-08 12:30:24.505359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48a1378f9dda'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('metadata_registry', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('metadata_registry', 'created_at')
    # ### end Alembic commands ###
