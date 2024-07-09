"""Init

Revision ID: 74db4139f8ef
Revises: 
Create Date: 2024-07-09 18:08:21.542738

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "74db4139f8ef"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=200), nullable=False),
        sa.Column("canonical_url", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel")),
    )
    op.create_table(
        "profile",
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=200), nullable=False),
        sa.Column("first_name", sa.String(length=200), nullable=False),
        sa.Column("last_name", sa.String(length=200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "blocked", "banned", "deleted", name="status"),
            nullable=False,
        ),
        sa.Column("subs_limit", sa.Integer(), nullable=False),
        sa.Column(
            "auth_timestamp",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profile")),
    )
    op.create_table(
        "profile_channel_association",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channel.id"],
            name=op.f("fk_profile_channel_association_channel_id_channel"),
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profile.id"],
            name=op.f("fk_profile_channel_association_profile_id_profile"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profile_channel_association")),
        sa.UniqueConstraint(
            "profile_id",
            "channel_id",
            name="profile_channel_association__profile_id_channel_id__uc",
        ),
    )
    op.create_table(
        "stream",
        sa.Column("url", sa.String(length=200), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"], ["channel.id"], name=op.f("fk_stream_channel_id_channel")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stream")),
        sa.UniqueConstraint("url", name=op.f("uq_stream_url")),
    )
    op.create_table(
        "video",
        sa.Column("url", sa.String(length=200), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"], ["channel.id"], name=op.f("fk_video_channel_id_channel")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_video")),
        sa.UniqueConstraint("url", name=op.f("uq_video_url")),
    )


def downgrade() -> None:
    op.drop_table("video")
    op.drop_table("stream")
    op.drop_table("profile_channel_association")
    op.drop_table("profile")
    op.drop_table("channel")
