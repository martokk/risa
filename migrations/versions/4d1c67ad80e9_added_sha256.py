"""added sha256

Revision ID: 4d1c67ad80e9
Revises: 200d91f6a040
Create Date: 2025-05-28 20:03:57.695449

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '4d1c67ad80e9'
down_revision = '200d91f6a040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sdextranetwork', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lora_sha256', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sdextranetwork', schema=None) as batch_op:
        batch_op.drop_column('lora_sha256')

    # ### end Alembic commands ###
