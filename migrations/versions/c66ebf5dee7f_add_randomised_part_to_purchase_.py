"""add_randomised_part_to_purchase_entrance_code

Revision ID: c66ebf5dee7f
Revises: c6c7509bb1f8
Create Date: 2020-07-08 15:20:09.869987

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c66ebf5dee7f'
down_revision = 'c6c7509bb1f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchase', sa.Column('entrance_code_randomised', sa.String(length=12), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('purchase', 'entrance_code_randomised')
    # ### end Alembic commands ###
