"""add_vat_to_purchase

Revision ID: 39f71f406904
Revises: eb0ea221aefa
Create Date: 2020-06-03 13:48:40.907726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39f71f406904'
down_revision = 'eb0ea221aefa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchase', sa.Column('vat_percentage', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('purchase', 'vat_percentage')
    # ### end Alembic commands ###
