"""updated to base_url

Revision ID: d25d4f326813
Revises: d7d6d70b5fd3
Create Date: 2025-06-23 23:25:11.283179

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = 'd25d4f326813'
down_revision = 'd7d6d70b5fd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new column as nullable
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # 2. Copy data from base_domain to base_url
    op.execute("UPDATE instancestate SET base_url = base_domain")
    # 3. Alter base_url to be non-nullable
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.alter_column('base_url', nullable=False)
        # 4. Drop old column
        batch_op.drop_column('base_domain')

    # ### end Alembic commands ###


def downgrade() -> None:
    # 1. Add old column as nullable
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_domain', sa.VARCHAR(), autoincrement=False, nullable=True))
    # 2. Copy data from base_url to base_domain
    op.execute("UPDATE instancestate SET base_domain = base_url")
    # 3. Alter base_domain to be non-nullable
    with op.batch_alter_table('instancestate', schema=None) as batch_op:
        batch_op.alter_column('base_domain', nullable=False)
        # 4. Drop new column
        batch_op.drop_column('base_url')

    # ### end Alembic commands ###
