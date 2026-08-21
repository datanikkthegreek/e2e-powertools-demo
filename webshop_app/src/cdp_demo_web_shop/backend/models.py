from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- Product ---


class ProductBase(SQLModel):
    name: str = Field(index=True)
    description: str
    price_eur: float = Field(description="Price in EUR")
    image_url: str


class Product(ProductBase, table=True):
    __tablename__ = "products"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    long_description: str | None = Field(default=None)
    specs: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class ProductOut(ProductBase):
    id: UUID


class ProductDetailOut(ProductOut):
    long_description: str | None = None
    specs: dict[str, Any] | None = None


# --- Account ---


class AccountBase(SQLModel):
    first_name: str
    surname: str
    street: str
    house_number: str
    postal_code: str
    city: str
    country: str
    date_of_birth: date
    email: str = Field(index=True, unique=True)


class Account(AccountBase, table=True):
    __tablename__ = "accounts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class AccountIn(BaseModel):
    first_name: str
    surname: str
    street: str
    house_number: str
    postal_code: str
    city: str
    country: str
    date_of_birth: date
    email: str


class AccountOut(AccountBase):
    id: UUID


# --- Cart ---


class Cart(SQLModel, table=True):
    __tablename__ = "carts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    status: str = Field(default="active", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cart_id: UUID | None = Field(default=None, foreign_key="carts.id", index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    product_id: UUID = Field(foreign_key="products.id", index=True)
    quantity: int = Field(default=1, ge=1)


class CartItemIn(BaseModel):
    product_id: UUID
    quantity: int = PydanticField(default=1, ge=1)


class CartItemPatch(BaseModel):
    quantity: int = PydanticField(ge=1)


class CartItemOut(BaseModel):
    id: UUID
    cart_id: UUID | None = None
    account_id: UUID
    product_id: UUID
    quantity: int
    product: ProductOut
    line_total_eur: float


# --- Purchase ---


class Purchase(SQLModel, table=True):
    __tablename__ = "purchases"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cart_id: UUID | None = Field(default=None, foreign_key="carts.id", index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    total_eur: float


class PurchaseLine(SQLModel, table=True):
    __tablename__ = "purchase_lines"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    purchase_id: UUID = Field(foreign_key="purchases.id", index=True)
    product_id: UUID = Field(foreign_key="products.id")
    name_snapshot: str
    unit_price_eur: float
    quantity: int


class PurchaseLineOut(BaseModel):
    id: UUID
    product_id: UUID
    name_snapshot: str
    unit_price_eur: float
    quantity: int
    line_total_eur: float


class PurchaseOut(BaseModel):
    id: UUID
    cart_id: UUID | None = None
    account_id: UUID
    account_name: str
    account_email: str
    created_at: datetime
    total_eur: float
    lines: list[PurchaseLineOut]


# --- Analytics ---


class AnalyticsOut(BaseModel):
    total_events: int
    page_views: int
    registrations: int
    purchases: int
    abandoned_carts: int


class TablePreviewOut(BaseModel):
    """A bounded preview of a Unity Catalog table for the Analytics page."""

    name: str
    fqn: str
    columns: list[str]
    rows: list[list[str | None]]
    row_limit: int
    truncated: bool


# --- Triggered pipeline job ---


class PipelineRunOut(BaseModel):
    """Result of triggering the cdp-triggered pipeline job via run_now."""

    run_id: int
    run_page_url: str | None = None


class PipelineRunStatusOut(BaseModel):
    """Live status of a triggered pipeline job run."""

    run_id: int
    life_cycle_state: str | None = None
    result_state: str | None = None
    finished: bool
