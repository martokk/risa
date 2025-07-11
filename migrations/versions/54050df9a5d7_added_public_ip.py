"""added public_ip

Revision ID: 54050df9a5d7
Revises: 06e2a61f1f06
Create Date: 2025-07-04 22:53:14.101053

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '54050df9a5d7'
down_revision = '06e2a61f1f06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('public_ip', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.drop_column('public_ip')

    # ### end Alembic commands ###
