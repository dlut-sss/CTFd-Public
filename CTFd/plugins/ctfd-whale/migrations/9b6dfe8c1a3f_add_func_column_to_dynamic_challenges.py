"""Add func column to dynamic_docker_challenges

Revision ID: 9b6dfe8c1a3f
Revises:
Create Date: 2024-02-27 15:05:23.133234

"""
import sqlalchemy as sa

from CTFd.plugins.migrations import get_columns_for_table
from sqlalchemy.engine.reflection import Inspector

revision = "9b6dfe8c1a3f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
    inspector = Inspector.from_engine(op.get_bind())
    tables = inspector.get_table_names()
def upgrade(op=None):
    inspector = Inspector.from_engine(op.get_bind())
    tables = inspector.get_table_names()

    if "dynamic_docker_challenge" not in tables:
        op.create_table(
            "dynamic_docker_challenge",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("initial", sa.Integer(), nullable=True, default=0),
            sa.Column("minimum", sa.Integer(), nullable=True, default=0),
            sa.Column("decay", sa.Integer(), nullable=True, default=0),
            sa.Column("memory_limit", sa.Text(), nullable=True, default="128m"),
            sa.Column("cpu_limit", sa.Float(), nullable=True, default=0.5),
            sa.Column("dynamic_score", sa.Integer(), nullable=True, default=0),
            sa.Column("docker_image", sa.Text(), nullable=True, default=""),
            sa.Column("redirect_type", sa.Text(), nullable=True, default=""),
            sa.Column("redirect_port", sa.Integer(), nullable=True, default=0),
            sa.Column("function", sa.String(length=32), nullable=True, default="logarithmic"),
            sa.ForeignKeyConstraint(["id"], ["challenges.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id")
        )
    else:
        # 表存在，执行更新操作
        columns = get_columns_for_table(
            op=op, table_name="dynamic_docker_challenge", names_only=True
        )
        if "function" not in columns:
            op.add_column(
                "dynamic_docker_challenge",
                sa.Column("function", sa.String(length=32), nullable=True),
            )
            conn = op.get_bind()
            url = str(conn.engine.url)
            if url.startswith("postgres"):
                conn.execute(
                    "UPDATE dynamic_docker_challenge SET function = 'logarithmic' WHERE function IS NULL"
                )
            else:
                conn.execute(
                    "UPDATE dynamic_docker_challenge SET `function` = 'logarithmic' WHERE `function` IS NULL"
                )


def downgrade(op=None):
    columns = get_columns_for_table(
        op=op, table_name="dynamic_docker_challenge", names_only=True
    )
    if "function" in columns:
        op.drop_column("dynamic_docker_challenge", "function")
