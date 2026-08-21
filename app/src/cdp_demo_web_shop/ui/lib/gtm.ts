import { ACTIVE_ACCOUNT_STORAGE_KEY } from "@/lib/active-account";
import type { AccountOut, CartItemOut, PurchaseOut } from "@/lib/api";

const DEFAULT_GA4_MEASUREMENT_ID = "G-16EKZCTX0K";
const DEFAULT_GTM_TRANSPORT_URL =
  "https://christian-ashby-gtm-reoceinrcq-ew.a.run.app";

export const GA4_MEASUREMENT_ID: string = (
  import.meta.env.VITE_GA4_MEASUREMENT_ID ?? DEFAULT_GA4_MEASUREMENT_ID
).trim();
export const GTM_TRANSPORT_URL: string = (
  import.meta.env.VITE_GTM_TRANSPORT_URL ?? DEFAULT_GTM_TRANSPORT_URL
).trim();

// Ingestion mode: "gtm" (default) sends events through Google Tag Manager via
// gtag/dataLayer. "zerobus" POSTs each event to the backend, which writes it to
// the gtm_events table through the Zerobus REST API.
export const INGESTION_MODE: string = (
  import.meta.env.VITE_INGESTION_MODE ?? "gtm"
)
  .trim()
  .toLowerCase();

const EVENTS_ENDPOINT = "/api/events";

const CURRENCY = "EUR";

type DataLayer = unknown[];
type Gtag = (...args: unknown[]) => void;

declare global {
  interface Window {
    dataLayer?: DataLayer;
    gtag?: Gtag;
  }
}

export function initDataLayer(): void {
  if (typeof window === "undefined") return;
  if (!Array.isArray(window.dataLayer)) {
    window.dataLayer = [];
  }
}

function initGtagFunction(): Gtag | null {
  if (typeof window === "undefined") return null;
  initDataLayer();
  if (!window.gtag) {
    window.gtag = function gtag() {
      window.dataLayer!.push(arguments);
    } as Gtag;
  }
  return window.gtag;
}

let gtagLoaded = false;

export function loadGtag(): void {
  if (typeof document === "undefined") return;
  if (INGESTION_MODE !== "gtm") return;
  if (gtagLoaded) return;
  if (!GA4_MEASUREMENT_ID) {
    console.warn(
      "[gtm] VITE_GA4_MEASUREMENT_ID is not set — skipping gtag script injection.",
    );
    return;
  }
  const gtag = initGtagFunction();
  if (!gtag) return;

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(GA4_MEASUREMENT_ID)}`;
  document.head.appendChild(script);

  gtag("js", new Date());
  gtag("config", GA4_MEASUREMENT_ID, {
    ...(GTM_TRANSPORT_URL ? { transport_url: GTM_TRANSPORT_URL } : {}),
    first_party_collection: false,
  });

  gtagLoaded = true;
}

function getDataLayer(): DataLayer | null {
  if (typeof window === "undefined") return null;
  initDataLayer();
  return window.dataLayer ?? null;
}

function readActiveAccountId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(ACTIVE_ACCOUNT_STORAGE_KEY);
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function flattenedEventParams(params: Record<string, unknown>): Record<string, unknown> {
  return {
    ...(isRecord(params.ecommerce) ? params.ecommerce : {}),
    ...params,
  };
}

function browserContext(): {
  page_location?: string;
  page_referrer?: string;
  page_title?: string;
  screen_resolution?: string;
  language?: string;
} {
  if (typeof window === "undefined") return {};
  const screenResolution =
    typeof screen !== "undefined" && screen.width && screen.height
      ? `${screen.width}x${screen.height}`
      : undefined;
  return {
    page_location: window.location?.href,
    page_referrer:
      typeof document !== "undefined" && document.referrer
        ? document.referrer
        : undefined,
    page_title:
      typeof document !== "undefined" ? document.title : undefined,
    screen_resolution: screenResolution,
    language:
      typeof navigator !== "undefined" ? navigator.language : undefined,
  };
}

// Fire-and-forget POST to the backend Zerobus ingestion endpoint. `keepalive`
// lets events fired during navigation/unload (e.g. abandon_cart) still flush.
function postZerobusEvent(
  eventName: string,
  webInputData: Record<string, unknown>,
): void {
  if (typeof fetch === "undefined") return;
  const context = browserContext();
  try {
    void fetch(EVENTS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_name: eventName,
        web_input_data: webInputData,
        ...context,
      }),
      keepalive: true,
    }).catch((error) => {
      console.warn("[zerobus] failed to send event", eventName, error);
    });
  } catch (error) {
    console.warn("[zerobus] failed to send event", eventName, error);
  }
}

function sendEvent(eventName: string, params: Record<string, unknown>): void {
  const webInputData = {
    event_name: eventName,
    timestamp: new Date().toISOString(),
    ...flattenedEventParams(params),
  };

  if (INGESTION_MODE === "zerobus") {
    postZerobusEvent(eventName, webInputData);
    return;
  }

  const gtag = initGtagFunction();
  if (!gtag) return;
  gtag("event", eventName, {
    ...webInputData,
    web_input_data: webInputData,
  });
}

function emailDerivedPayload(email: string): {
  email: string;
  name_surname?: string;
  domain?: string;
} {
  const trimmedEmail = email.trim();
  const atIndex = trimmedEmail.indexOf("@");
  if (atIndex <= 0 || atIndex === trimmedEmail.length - 1) {
    return { email: trimmedEmail };
  }
  return {
    email: trimmedEmail,
    name_surname: trimmedEmail.slice(0, atIndex),
    domain: trimmedEmail.slice(atIndex),
  };
}

function nameDerivedPayload(name: string): {
  first_name?: string;
  surname?: string;
} {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return {};
  if (parts.length === 1) return { first_name: parts[0] };
  return {
    first_name: parts[0],
    surname: parts.slice(1).join(" "),
  };
}

function clearEcommerce(): void {
  const dl = getDataLayer();
  if (!dl) return;
  dl.push({ ecommerce: null });
}

interface ProductLike {
  id: string;
  name: string;
  price_eur: number;
}

function productToItem(product: ProductLike, quantity?: number) {
  return {
    item_id: product.id,
    item_name: product.name,
    price: product.price_eur,
    currency: CURRENCY,
    ...(quantity !== undefined ? { quantity } : {}),
  };
}

function flattenedItemPayload(product: ProductLike, quantity: number) {
  return {
    item_id: product.id,
    item_name: product.name,
    price: product.price_eur,
    currency: CURRENCY,
    item_quantity: quantity,
    items: [productToItem(product, quantity)],
  };
}

export function trackPageView(params: {
  path: string;
  title?: string;
  account_id?: string | null;
}): void {
  const userId = params.account_id ?? readActiveAccountId();
  sendEvent("page_view", {
    ...(userId ? { user_id: userId } : {}),
    page_path: params.path,
    page_title: params.title ?? (typeof document !== "undefined" ? document.title : undefined),
    page_location:
      typeof window !== "undefined" ? window.location.href : undefined,
  });
}

export function trackViewItem(params: {
  product: ProductLike;
  account_id?: string | null;
}): void {
  const userId = params.account_id ?? readActiveAccountId();
  clearEcommerce();
  sendEvent("view_item", {
    ...(userId ? { user_id: userId } : {}),
    ecommerce: {
      currency: CURRENCY,
      value: params.product.price_eur,
      items: [productToItem(params.product)],
    },
  });
}

export function trackAddToCart(params: {
  product: ProductLike;
  quantity: number;
  cart_id?: string | null;
  account_id?: string | null;
  previous_quantity?: number;
  new_quantity?: number;
  quantity_delta?: number;
  cart_action?: "added" | "quantity_increase" | "quantity_decrease" | "remove_item";
}): void {
  const userId = params.account_id ?? readActiveAccountId();
  const itemPayload = flattenedItemPayload(params.product, params.quantity);
  const previousQuantity = params.previous_quantity ?? 0;
  const newQuantity = params.new_quantity ?? params.quantity;
  const quantityDelta = params.quantity_delta ?? params.quantity;
  clearEcommerce();
  sendEvent("add_to_cart", {
    ...(userId ? { user_id: userId } : {}),
    ...(params.cart_id ? { cart_id: params.cart_id } : {}),
    ...itemPayload,
    previous_quantity: previousQuantity,
    new_quantity: newQuantity,
    quantity_delta: quantityDelta,
    cart_action: params.cart_action ?? "added",
    ecommerce: {
      ...(params.cart_id ? { cart_id: params.cart_id } : {}),
      currency: itemPayload.currency,
      value: params.product.price_eur * params.quantity,
      items: itemPayload.items,
    },
  });
}

export function trackCartQuantityChange(params: {
  item: CartItemOut;
  previous_quantity: number;
  new_quantity: number;
  account_id?: string | null;
  cart_action?: "quantity_increase" | "quantity_decrease" | "remove_item";
}): void {
  const quantityDelta = params.new_quantity - params.previous_quantity;
  if (quantityDelta === 0) {
    return;
  }

  trackAddToCart({
    product: params.item.product,
    quantity: Math.abs(quantityDelta),
    cart_id: params.item.cart_id,
    account_id: params.account_id,
    previous_quantity: params.previous_quantity,
    new_quantity: params.new_quantity,
    quantity_delta: quantityDelta,
    cart_action:
      params.cart_action ??
      (quantityDelta > 0 ? "quantity_increase" : "quantity_decrease"),
  });
}

export function trackPurchase(params: {
  purchase: PurchaseOut;
  account_id?: string | null;
}): void {
  const userId = params.account_id ?? params.purchase.account_id ?? readActiveAccountId();
  const cartId = params.purchase.cart_id;
  clearEcommerce();
  sendEvent("purchase", {
    ...(userId ? { user_id: userId } : {}),
    ...(cartId ? { cart_id: cartId } : {}),
    ...emailDerivedPayload(params.purchase.account_email),
    ...nameDerivedPayload(params.purchase.account_name),
    ecommerce: {
      ...(cartId ? { cart_id: cartId } : {}),
      transaction_id: params.purchase.id,
      currency: CURRENCY,
      value: params.purchase.total_eur,
      items: params.purchase.lines.map((line) => ({
        item_id: line.product_id,
        item_name: line.name_snapshot,
        price: line.unit_price_eur,
        currency: CURRENCY,
        quantity: line.quantity,
      })),
    },
  });
}

export function trackPurchaseDeleted(params: { purchase: PurchaseOut }): void {
  sendEvent("purchase_deleted", {
    user_id: params.purchase.account_id,
    transaction_id: params.purchase.id,
    cart_id: params.purchase.cart_id,
    ...emailDerivedPayload(params.purchase.account_email),
    currency: CURRENCY,
    value: params.purchase.total_eur,
  });
}

export function trackAbandonCart(params: {
  items: CartItemOut[];
  account_id?: string | null;
}): void {
  const userId = params.account_id ?? readActiveAccountId();
  const cartId = params.items.find((item) => item.cart_id)?.cart_id;
  const value = params.items.reduce((acc, i) => acc + i.line_total_eur, 0);
  clearEcommerce();
  sendEvent("abandon_cart", {
    ...(userId ? { user_id: userId } : {}),
    ...(cartId ? { cart_id: cartId } : {}),
    ecommerce: {
      ...(cartId ? { cart_id: cartId } : {}),
      currency: CURRENCY,
      value: Number(value.toFixed(2)),
      items: params.items.map((i) => ({
        item_id: i.product_id,
        item_name: i.product.name,
        price: i.product.price_eur,
        currency: CURRENCY,
        quantity: i.quantity,
      })),
    },
  });
}

export function trackAccountSelected(params: {
  account_id: string;
  source: "auto" | "manual";
}): void {
  sendEvent("account_selected", {
    user_id: params.account_id,
    account_id: params.account_id,
    selection_source: params.source,
  });
}

function accountIdentityPayload(account: AccountOut) {
  return {
    user_id: account.id,
    ...emailDerivedPayload(account.email),
    first_name: account.first_name,
    surname: account.surname,
    city: account.city,
    country: account.country,
  };
}

export function trackSignUp(params: { account: AccountOut }): void {
  sendEvent("sign_up", {
    method: "form",
    ...accountIdentityPayload(params.account),
  });
}

export function trackAccountDeleted(params: { account: AccountOut }): void {
  sendEvent("account_deleted", {
    method: "self_service",
    ...accountIdentityPayload(params.account),
  });
}
