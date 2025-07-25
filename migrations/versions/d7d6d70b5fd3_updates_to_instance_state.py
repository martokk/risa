"""updates to instance state

Revision ID: d7d6d70b5fd3
Revises: ac90a7b9ec81
Create Date: 2025-06-18 01:22:01.514514

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = 'd7d6d70b5fd3'
down_revision = 'ac90a7b9ec81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('runpod_gpu_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('runpod_pod_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('runpod_public_ip', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.drop_column('runpod_instance_id')
        batch_op.drop_column('runpod_instance_ip')

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('runpod_instance_ip', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('runpod_instance_id', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.drop_column('runpod_public_ip')
        batch_op.drop_column('runpod_pod_id')
        batch_op.drop_column('runpod_gpu_name')

    # ### end Alembic commands ###
