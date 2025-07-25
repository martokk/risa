"""renamed remote_file_path to download_url

Revision ID: 21887c304c0e
Revises: f20c9dced3eb
Create Date: 2025-07-02 12:22:49.708656

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '21887c304c0e'
down_revision = 'f20c9dced3eb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sdcheckpoint', schema=None) as batch_op:
        batch_op.add_column(sa.Column('download_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # Copy data from remote_file_path to download_url
    op.execute("UPDATE sdcheckpoint SET download_url = remote_file_path")
    with op.batch_alter_table('sdcheckpoint', schema=None) as batch_op:
        batch_op.drop_column('remote_file_path')

    with op.batch_alter_table('sdextranetwork', schema=None) as batch_op:
        batch_op.add_column(sa.Column('download_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # Copy data from remote_file_path to download_url
    op.execute("UPDATE sdextranetwork SET download_url = remote_file_path")
    with op.batch_alter_table('sdextranetwork', schema=None) as batch_op:
        batch_op.drop_column('remote_file_path')

    # ### end Alembic commands ###alem


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sdextranetwork', schema=None) as batch_op:
        batch_op.add_column(sa.Column('remote_file_path', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.drop_column('download_url')

    with op.batch_alter_table('sdcheckpoint', schema=None) as batch_op:
        batch_op.add_column(sa.Column('remote_file_path', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.drop_column('download_url')

    # ### end Alembic commands ###
