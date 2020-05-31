"""remove_party_id_from_file_table

Revision ID: 44e0c349a1a1
Revises: 711bc211f5b1
Create Date: 2020-04-21 23:29:48.179238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '44e0c349a1a1'
down_revision = '711bc211f5b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('file_ibfk_1', 'file', type_='foreignkey')
    op.drop_column('file', 'party_id')
    op.add_column('party', sa.Column('logo_id', sa.Integer(), nullable=True))
    op.create_foreign_key('party_ibfk_3', 'party', 'file', ['logo_id'], ['file_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('party_ibfk_3', 'party', type_='foreignkey')
    op.drop_column('party', 'logo_id')
    op.add_column('file', sa.Column('party_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('file_ibfk_1', 'file', 'party', ['party_id'], ['party_id'])
    # ### end Alembic commands ###
