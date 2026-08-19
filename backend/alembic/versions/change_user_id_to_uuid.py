"""change_user_id_to_uuid

Revision ID: a1b2c3d4e5f6
Revises: 4047349d13b1
Create Date: 2026-08-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4047349d13b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: change User.id from Integer to UUID and update Booking.user_id foreign key."""
    # Step 1: Add new UUID column to users
    op.add_column('users', sa.Column('id_new', postgresql.UUID(as_uuid=True), nullable=True))

    # Step 2: Generate UUIDs for all existing users
    op.execute("UPDATE users SET id_new = gen_random_uuid()")

    # Step 3: Create temp mapping table (old int id -> new UUID)
    op.execute("""
        CREATE TABLE user_id_mapping AS
        SELECT id::integer as old_id, id_new as new_id
        FROM users
    """)

    # Step 4: Drop foreign key
    op.drop_constraint('bookings_user_id_fkey', 'bookings', type_='foreignkey')

    # Step 5: Add temp column to store old user_id values
    op.add_column('bookings', sa.Column('user_id_old', sa.Integer(), nullable=True))
    op.execute("UPDATE bookings SET user_id_old = user_id")

    # Step 6: Drop user_id column
    op.drop_column('bookings', 'user_id')

    # Step 7: Add user_id as UUID
    op.add_column('bookings', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False))

    # Step 8: Update bookings with UUIDs using mapping table (joining on old integer id)
    op.execute("""
        UPDATE bookings
        SET user_id = user_id_mapping.new_id
        FROM user_id_mapping
        WHERE bookings.user_id_old = user_id_mapping.old_id
    """)

    # Step 9: Drop temp column
    op.drop_column('bookings', 'user_id_old')

    # Step 10: Drop old users.id column
    op.drop_column('users', 'id')

    # Step 11: Rename id_new to id
    op.alter_column('users', 'id_new', new_column_name='id')

    # Step 12: Drop mapping table
    op.execute("DROP TABLE user_id_mapping")

    # Step 13: Re-create primary key on users.id
    op.execute("ALTER TABLE users ADD PRIMARY KEY (id)")

    # Step 14: Re-create foreign key
    op.create_foreign_key(
        'bookings_user_id_fkey',
        'bookings', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema: revert User.id from UUID back to Integer."""
    # Note: This will generate new sequential IDs, original IDs will be lost
    # Step 1: Drop foreign key
    op.drop_constraint('bookings_user_id_fkey', 'bookings', type_='foreignkey')

    # Step 2: Add new integer column to users
    op.add_column('users', sa.Column('id_old', sa.Integer(), nullable=True))

    # Step 3: Generate sequential IDs
    op.execute("""
        UPDATE users
        SET id_old = row_number() OVER (ORDER BY id)
    """)

    # Step 4: Add temp column to bookings
    op.add_column('bookings', sa.Column('user_id_old', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE bookings SET user_id_old = user_id")

    # Step 5: Drop UUID user_id column
    op.drop_column('bookings', 'user_id')

    # Step 6: Add Integer user_id column
    op.add_column('bookings', sa.Column('user_id', sa.Integer(), nullable=False))

    # Step 7: Update user_id using subquery
    op.execute("""
        UPDATE bookings
        SET user_id = users.id_old
        FROM users
        WHERE bookings.user_id_old = users.id
    """)

    # Step 8: Drop temp column
    op.drop_column('bookings', 'user_id_old')

    # Step 9: Drop UUID column
    op.drop_column('users', 'id')

    # Step 10: Rename id_old to id
    op.alter_column('users', 'id_old', new_column_name='id')

    # Step 11: Recreate foreign key
    op.create_foreign_key(
        'bookings_user_id_fkey',
        'bookings', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
