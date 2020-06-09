"""add_phone_number_to_user

Revision ID: 0d05d2d77bfa
Revises: c0f7c2e16338
Create Date: 2020-06-09 17:06:17.335843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d05d2d77bfa'
down_revision = 'c0f7c2e16338'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('phone_number', sa.String(length=256), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'phone_number')
    # ### end Alembic commands ###
