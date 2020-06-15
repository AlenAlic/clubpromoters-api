"""add_bookkeeping_program_email_to_config

Revision ID: 24458728adf1
Revises: ef56810ada80
Create Date: 2020-06-15 19:09:21.997964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24458728adf1'
down_revision = 'ef56810ada80'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('bookkeeping_program_email', sa.String(length=256), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('configuration', 'bookkeeping_program_email')
    # ### end Alembic commands ###