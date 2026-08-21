from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from databricks.sdk.service.iam import User as UserOut
from fastapi import HTTPException, Path, status
from sqlalchemy import delete as sa_delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from .core import Dependencies, create_router
from .models import (
    Account,
    AccountIn,
    AccountOut,
    Cart,
    CartItem,
    CartItemIn,
    CartItemOut,
    CartItemPatch,
    Product,
    ProductDetailOut,
    ProductOut,
    Purchase,
    PurchaseLine,
    PurchaseLineOut,
    PurchaseOut,
    VersionOut,
)

router = create_router()

AccountIdParam = Annotated[UUID, Path(description="Account ID")]
ProductIdParam = Annotated[UUID, Path(description="Product ID")]
PurchaseIdParam = Annotated[UUID, Path(description="Purchase ID")]


# --- Meta ---


@router.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@router.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(user_ws: Dependencies.UserClient):
    return user_ws.current_user.me()


# --- Products ---


@router.get("/products", response_model=list[ProductOut], operation_id="listProducts")
def list_products(session: Dependencies.Session) -> list[ProductOut]:
    products = session.exec(select(Product).order_by(col(Product.name))).all()
    return [ProductOut.model_validate(p, from_attributes=True) for p in products]


@router.get(
    "/products/{product_id}",
    response_model=ProductDetailOut,
    operation_id="getProduct",
)
def get_product(
    product_id: ProductIdParam, session: Dependencies.Session
) -> ProductDetailOut:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(product, from_attributes=True)


# --- Accounts ---


@router.get("/accounts", response_model=list[AccountOut], operation_id="listAccounts")
def list_accounts(session: Dependencies.Session) -> list[AccountOut]:
    accounts = session.exec(
        select(Account).order_by(col(Account.surname), col(Account.first_name))
    ).all()
    return [AccountOut.model_validate(a, from_attributes=True) for a in accounts]


@router.post(
    "/accounts",
    response_model=AccountOut,
    operation_id="createAccount",
    status_code=status.HTTP_201_CREATED,
)
def create_account(payload: AccountIn, session: Dependencies.Session) -> AccountOut:
    account = Account(
        first_name=payload.first_name,
        surname=payload.surname,
        street=payload.street,
        house_number=payload.house_number,
        postal_code=payload.postal_code,
        city=payload.city,
        country=payload.country,
        date_of_birth=payload.date_of_birth,
        email=payload.email,
    )
    session.add(account)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with email '{payload.email}' already exists",
        )
    session.refresh(account)
    return AccountOut.model_validate(account, from_attributes=True)


@router.get(
    "/accounts/{account_id}",
    response_model=AccountOut,
    operation_id="getAccount",
)
def get_account(account_id: AccountIdParam, session: Dependencies.Session) -> AccountOut:
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountOut.model_validate(account, from_attributes=True)


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteAccount",
)
def delete_account(
    account_id: AccountIdParam, session: Dependencies.Session
) -> None:
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    has_purchase = session.exec(
        select(Purchase).where(col(Purchase.account_id) == account_id).limit(1)
    ).first()
    if has_purchase is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete account with purchases",
        )

    session.execute(
        sa_delete(CartItem).where(col(CartItem.account_id) == account_id)
    )
    session.execute(sa_delete(Cart).where(col(Cart.account_id) == account_id))
    session.delete(account)
    session.commit()


# --- Cart helpers ---


def _cart_item_out(item: CartItem, product: Product) -> CartItemOut:
    return CartItemOut(
        id=item.id,
        cart_id=item.cart_id,
        account_id=item.account_id,
        product_id=item.product_id,
        quantity=item.quantity,
        product=ProductOut.model_validate(product, from_attributes=True),
        line_total_eur=round(product.price_eur * item.quantity, 2),
    )


def _require_account(session, account_id: UUID) -> Account:
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def _require_product(session, product_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _active_cart(session, account_id: UUID) -> Cart | None:
    return session.exec(
        select(Cart)
        .where(col(Cart.account_id) == account_id)
        .where(col(Cart.status) == "active")
        .order_by(col(Cart.updated_at).desc())
    ).first()


def _get_or_create_active_cart(session, account_id: UUID) -> Cart:
    cart = _active_cart(session, account_id)
    if cart is not None:
        return cart

    cart = Cart(account_id=account_id)
    session.add(cart)
    session.flush()
    return cart


def _touch_cart(session, cart: Cart, when: datetime | None = None) -> None:
    cart.updated_at = when or _now_utc()
    session.add(cart)


# --- Cart ---


@router.get(
    "/accounts/{account_id}/cart",
    response_model=list[CartItemOut],
    operation_id="getCart",
)
def get_cart(
    account_id: AccountIdParam, session: Dependencies.Session
) -> list[CartItemOut]:
    _require_account(session, account_id)
    cart = _active_cart(session, account_id)
    if cart is None:
        return []

    rows = session.exec(
        select(CartItem, Product)
        .join(Product, onclause=col(Product.id) == col(CartItem.product_id))
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
        .order_by(col(Product.name))
    ).all()
    return [_cart_item_out(item, product) for item, product in rows]


@router.post(
    "/accounts/{account_id}/cart",
    response_model=CartItemOut,
    operation_id="addToCart",
)
def add_to_cart(
    account_id: AccountIdParam,
    payload: CartItemIn,
    session: Dependencies.Session,
) -> CartItemOut:
    _require_account(session, account_id)
    product = _require_product(session, payload.product_id)
    cart = _get_or_create_active_cart(session, account_id)

    existing = session.exec(
        select(CartItem)
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
        .where(col(CartItem.product_id) == payload.product_id)
    ).first()

    if existing is None:
        item = CartItem(
            cart_id=cart.id,
            account_id=account_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        session.add(item)
    else:
        existing.quantity += payload.quantity
        item = existing

    _touch_cart(session, cart)
    session.commit()
    session.refresh(item)
    return _cart_item_out(item, product)


@router.patch(
    "/accounts/{account_id}/cart/{product_id}",
    response_model=CartItemOut,
    operation_id="updateCartItem",
)
def update_cart_item(
    account_id: AccountIdParam,
    product_id: ProductIdParam,
    payload: CartItemPatch,
    session: Dependencies.Session,
) -> CartItemOut:
    _require_account(session, account_id)
    product = _require_product(session, product_id)
    cart = _active_cart(session, account_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item = session.exec(
        select(CartItem)
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
        .where(col(CartItem.product_id) == product_id)
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = payload.quantity
    session.add(item)
    _touch_cart(session, cart)
    session.commit()
    session.refresh(item)
    return _cart_item_out(item, product)


@router.delete(
    "/accounts/{account_id}/cart/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="removeCartItem",
)
def remove_cart_item(
    account_id: AccountIdParam,
    product_id: ProductIdParam,
    session: Dependencies.Session,
) -> None:
    _require_account(session, account_id)
    cart = _active_cart(session, account_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item = session.exec(
        select(CartItem)
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
        .where(col(CartItem.product_id) == product_id)
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    session.delete(item)
    _touch_cart(session, cart)
    session.commit()


@router.delete(
    "/accounts/{account_id}/cart",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="clearCart",
)
def clear_cart(
    account_id: AccountIdParam, session: Dependencies.Session
) -> None:
    _require_account(session, account_id)
    cart = _active_cart(session, account_id)
    if cart is None:
        return

    session.execute(
        sa_delete(CartItem)
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
    )
    cart.status = "abandoned"
    _touch_cart(session, cart)
    session.commit()


# --- Checkout ---


@router.post(
    "/accounts/{account_id}/checkout",
    response_model=PurchaseOut,
    operation_id="checkout",
)
def checkout(
    account_id: AccountIdParam, session: Dependencies.Session
) -> PurchaseOut:
    account = _require_account(session, account_id)
    cart = _active_cart(session, account_id)
    if cart is None:
        raise HTTPException(status_code=400, detail="Cart is empty")

    rows = session.exec(
        select(CartItem, Product)
        .join(Product, onclause=col(Product.id) == col(CartItem.product_id))
        .where(col(CartItem.account_id) == account_id)
        .where(col(CartItem.cart_id) == cart.id)
    ).all()
    if not rows:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = round(sum(p.price_eur * c.quantity for c, p in rows), 2)
    purchased_at = _now_utc()
    purchase = Purchase(
        cart_id=cart.id,
        account_id=account_id,
        created_at=purchased_at,
        total_eur=total,
    )
    session.add(purchase)
    session.flush()

    lines = [
        PurchaseLine(
            purchase_id=purchase.id,
            product_id=p.id,
            name_snapshot=p.name,
            unit_price_eur=p.price_eur,
            quantity=c.quantity,
        )
        for c, p in rows
    ]
    for line in lines:
        session.add(line)

    for cart_item, _ in rows:
        session.delete(cart_item)

    cart.status = "purchased"
    _touch_cart(session, cart, purchased_at)
    session.commit()
    session.refresh(purchase)

    return PurchaseOut(
        id=purchase.id,
        cart_id=purchase.cart_id,
        account_id=purchase.account_id,
        account_name=f"{account.first_name} {account.surname}",
        account_email=account.email,
        created_at=purchase.created_at,
        total_eur=purchase.total_eur,
        lines=[
            PurchaseLineOut(
                id=line.id,
                product_id=line.product_id,
                name_snapshot=line.name_snapshot,
                unit_price_eur=line.unit_price_eur,
                quantity=line.quantity,
                line_total_eur=round(line.unit_price_eur * line.quantity, 2),
            )
            for line in lines
        ],
    )


# --- Purchases ---


@router.get(
    "/purchases",
    response_model=list[PurchaseOut],
    operation_id="listPurchases",
)
def list_purchases(session: Dependencies.Session) -> list[PurchaseOut]:
    rows = session.exec(
        select(Purchase, Account)
        .join(Account, onclause=col(Account.id) == col(Purchase.account_id))
        .order_by(col(Purchase.created_at).desc())
    ).all()
    if not rows:
        return []

    purchase_ids = [p.id for p, _ in rows]
    line_rows = session.exec(
        select(PurchaseLine).where(col(PurchaseLine.purchase_id).in_(purchase_ids))
    ).all()
    lines_by_purchase: dict = {}
    for line in line_rows:
        lines_by_purchase.setdefault(line.purchase_id, []).append(line)

    out: list[PurchaseOut] = []
    for purchase, account in rows:
        purchase_lines = lines_by_purchase.get(purchase.id, [])
        out.append(
            PurchaseOut(
                id=purchase.id,
                cart_id=purchase.cart_id,
                account_id=purchase.account_id,
                account_name=f"{account.first_name} {account.surname}",
                account_email=account.email,
                created_at=purchase.created_at,
                total_eur=purchase.total_eur,
                lines=[
                    PurchaseLineOut(
                        id=line.id,
                        product_id=line.product_id,
                        name_snapshot=line.name_snapshot,
                        unit_price_eur=line.unit_price_eur,
                        quantity=line.quantity,
                        line_total_eur=round(
                            line.unit_price_eur * line.quantity, 2
                        ),
                    )
                    for line in purchase_lines
                ],
            )
        )
    return out


@router.delete(
    "/purchases/{purchase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deletePurchase",
)
def delete_purchase(
    purchase_id: PurchaseIdParam, session: Dependencies.Session
) -> None:
    purchase = session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found")

    session.execute(
        sa_delete(PurchaseLine).where(col(PurchaseLine.purchase_id) == purchase_id)
    )
    session.delete(purchase)
    session.commit()
