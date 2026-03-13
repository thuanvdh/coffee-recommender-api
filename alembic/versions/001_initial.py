"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Coffee Shops table
    op.create_table(
        "coffee_shops",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("opening_hours", sa.String(length=100), nullable=True),
        sa.Column("price_range", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="open",
        ),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coffee_shops_name", "coffee_shops", ["name"])
    op.create_index("ix_coffee_shops_slug", "coffee_shops", ["slug"], unique=True)
    op.create_index("ix_coffee_shops_district", "coffee_shops", ["district"])
    op.create_index("ix_coffee_shops_status", "coffee_shops", ["status"])

    # Shop Purposes table
    op.create_table(
        "shop_purposes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["coffee_shops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_purposes_purpose", "shop_purposes", ["purpose"])

    # Shop Spaces table
    op.create_table(
        "shop_spaces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=False),
        sa.Column("space_type", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["coffee_shops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_spaces_space_type", "shop_spaces", ["space_type"])

    # Shop Amenities table
    op.create_table(
        "shop_amenities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=False),
        sa.Column("amenity", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["coffee_shops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_amenities_amenity", "shop_amenities", ["amenity"])


def downgrade() -> None:
    op.drop_table("shop_amenities")
    op.drop_table("shop_spaces")
    op.drop_table("shop_purposes")
    op.drop_table("coffee_shops")
