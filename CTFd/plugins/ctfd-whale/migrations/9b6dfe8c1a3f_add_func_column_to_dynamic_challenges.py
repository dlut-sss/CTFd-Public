"""Add func column to dynamic_docker_challenges

Revision ID: 9b6dfe8c1a3f
Revises:
Create Date: 2024-02-27 15:05:23.133234

"""
import sqlalchemy as sa

from CTFd.plugins.migrations import get_columns_for_table

revision = "9b6dfe8c1a3f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
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
