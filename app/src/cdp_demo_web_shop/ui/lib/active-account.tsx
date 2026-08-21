import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

import { useListAccounts } from "@/lib/api";

export const ACTIVE_ACCOUNT_STORAGE_KEY = "bosch_shop_active_account_id";
const STORAGE_KEY = ACTIVE_ACCOUNT_STORAGE_KEY;
const CHANGE_EVENT = "bosch-shop:active-account-changed";

// Module-level event bus so non-React code (e.g. a global QueryCache error
// handler in main.tsx) can imperatively clear the active account and have
// the provider re-render in the same tab. The native `storage` event only
// fires in *other* tabs, so we need this for current-tab updates.
const accountBus =
  typeof window !== "undefined" ? new EventTarget() : null;

function writeStorage(id: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (id) {
      window.localStorage.setItem(STORAGE_KEY, id);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    /* localStorage might be disabled — ignore */
  }
}

/**
 * Clear the active account from localStorage and notify the provider so the
 * current tab re-renders. Safe to call from anywhere — including the global
 * react-query error handler when the server returns 404 "Account not found".
 */
export function clearActiveAccountId(): void {
  writeStorage(null);
  accountBus?.dispatchEvent(
    new CustomEvent<string | null>(CHANGE_EVENT, { detail: null }),
  );
}

interface ActiveAccountCtx {
  activeAccountId: string | null;
  setActiveAccountId: (id: string | null) => void;
}

const Ctx = createContext<ActiveAccountCtx | null>(null);

export function ActiveAccountProvider({ children }: { children: ReactNode }) {
  const [activeAccountId, setActiveAccountIdState] = useState<string | null>(
    () => {
      if (typeof window === "undefined") return null;
      return window.localStorage.getItem(STORAGE_KEY);
    },
  );

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setActiveAccountIdState(e.newValue);
      }
    };
    const onBus = (e: Event) => {
      setActiveAccountIdState((e as CustomEvent<string | null>).detail);
    };
    window.addEventListener("storage", onStorage);
    accountBus?.addEventListener(CHANGE_EVENT, onBus);
    return () => {
      window.removeEventListener("storage", onStorage);
      accountBus?.removeEventListener(CHANGE_EVENT, onBus);
    };
  }, []);

  const setActiveAccountId = useCallback((id: string | null) => {
    writeStorage(id);
    setActiveAccountIdState(id);
  }, []);

  // Central reconciliation against the authoritative accounts list. This runs
  // app-wide (not gated behind the account picker's Suspense boundary), so a
  // stale cached id — e.g. left in localStorage by an earlier session on a
  // wiped/ephemeral DB — is corrected to a real account before it can cause a
  // 404 round-trip and the picker "snap-back". Same query key as the picker,
  // so react-query dedupes the request.
  const { data: accountsResponse } = useListAccounts();
  const accounts = accountsResponse?.data;
  useEffect(() => {
    if (!accounts) return;
    if (accounts.length === 0) {
      if (activeAccountId !== null) setActiveAccountId(null);
      return;
    }
    const isValid = accounts.some((a) => a.id === activeAccountId);
    if (!isValid) {
      setActiveAccountId(accounts[0].id);
    }
  }, [accounts, activeAccountId, setActiveAccountId]);

  return (
    <Ctx.Provider value={{ activeAccountId, setActiveAccountId }}>
      {children}
    </Ctx.Provider>
  );
}

export function useActiveAccount(): ActiveAccountCtx {
  const ctx = useContext(Ctx);
  if (!ctx) {
    throw new Error(
      "useActiveAccount must be used within ActiveAccountProvider",
    );
  }
  return ctx;
}
