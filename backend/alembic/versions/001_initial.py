"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("phone", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_order_date", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_city", "customers", ["city"])

    op.create_table(
        "orders",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("items", sa.JSON(), server_default="[]"),
        sa.Column("channel", sa.String(), server_default="online"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])

    op.create_table(
        "segments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), server_default=""),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("customer_count", sa.Integer(), server_default="0"),
        sa.Column("created_by_ai", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("segment_id", sa.String(), sa.ForeignKey("segments.id"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="draft"),
        sa.Column("total_sent", sa.Integer(), server_default="0"),
        sa.Column("total_delivered", sa.Integer(), server_default="0"),
        sa.Column("total_failed", sa.Integer(), server_default="0"),
        sa.Column("total_opened", sa.Integer(), server_default="0"),
        sa.Column("total_read", sa.Integer(), server_default="0"),
        sa.Column("total_clicked", sa.Integer(), server_default="0"),
        sa.Column("total_converted", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("launched_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.create_table(
        "communications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("campaign_id", sa.String(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="queued"),
        sa.Column("queued_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.Column("opened_at", sa.DateTime()),
        sa.Column("read_at", sa.DateTime()),
        sa.Column("clicked_at", sa.DateTime()),
        sa.Column("converted_at", sa.DateTime()),
        sa.Column("failed_at", sa.DateTime()),
    )
    op.create_index("ix_communications_campaign_id", "communications", ["campaign_id"])
    op.create_index("ix_communications_status", "communications", ["status"])


def downgrade() -> None:
    op.drop_table("communications")
    op.drop_table("campaigns")
    op.drop_table("segments")
    op.drop_table("orders")
    op.drop_table("customers")
