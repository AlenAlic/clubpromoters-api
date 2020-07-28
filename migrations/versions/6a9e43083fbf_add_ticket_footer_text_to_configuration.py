"""add_ticket_footer_text_to_configuration

Revision ID: 6a9e43083fbf
Revises: f2a79ae10ae1
Create Date: 2020-07-27 15:53:34.106699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a9e43083fbf'
down_revision = 'f2a79ae10ae1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('ticket_footer_text', sa.String(length=256), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('configuration', 'ticket_footer_text')
    # ### end Alembic commands ###