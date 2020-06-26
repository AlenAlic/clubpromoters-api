"""add_max_party_repeats_to_config

Revision ID: 94373df809b1
Revises: f01e57191aa1
Create Date: 2020-06-24 16:54:58.666986

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94373df809b1'
down_revision = 'f01e57191aa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('max_party_repeats', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('configuration', 'max_party_repeats')
    # ### end Alembic commands ###