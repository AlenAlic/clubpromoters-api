"""reword_invoice_to_receipt

Revision ID: aeb811c4cf2c
Revises: cf75235c7223
Create Date: 2020-06-08 21:44:13.068275

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'aeb811c4cf2c'
down_revision = 'cf75235c7223'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('receipt_address', sa.String(length=128), nullable=True))
    op.add_column('configuration', sa.Column('receipt_country', sa.String(length=128), nullable=True))
    op.add_column('configuration', sa.Column('receipt_phone', sa.String(length=128), nullable=True))
    op.add_column('configuration', sa.Column('receipt_title', sa.String(length=128), nullable=True))
    op.drop_column('configuration', 'invoice_address')
    op.drop_column('configuration', 'invoice_country')
    op.drop_column('configuration', 'invoice_title')
    op.drop_column('configuration', 'invoice_phone')
    op.add_column('purchase', sa.Column('receipt_path', sa.String(length=512), nullable=True))
    op.drop_column('purchase', 'invoice_path')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchase', sa.Column('invoice_path', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=512), nullable=True))
    op.drop_column('purchase', 'receipt_path')
    op.add_column('configuration', sa.Column('invoice_phone', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True))
    op.add_column('configuration', sa.Column('invoice_title', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True))
    op.add_column('configuration', sa.Column('invoice_country', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True))
    op.add_column('configuration', sa.Column('invoice_address', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True))
    op.drop_column('configuration', 'receipt_title')
    op.drop_column('configuration', 'receipt_phone')
    op.drop_column('configuration', 'receipt_country')
    op.drop_column('configuration', 'receipt_address')
    # ### end Alembic commands ###
