import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@/styles/globals.css";
import { routeTree } from "@/types/routeTree.gen";

import { RouterProvider, createRouter } from "@tanstack/react-router";
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { ApiError, listAccountsKey } from "@/lib/api";
import { initDataLayer, loadGtag, trackPageView } from "@/lib/gtm";

initDataLayer();
loadGtag();

function isAccountNotFound(error: unknown): boolean {
  if (!(error instanceof ApiError) || error.status !== 404) return false;
  const body = error.body as { detail?: string } | null | undefined;
  return body?.detail === "Account not found";
}

// When any account-scoped request 404s with "Account not found" — typically a
// stale active-account id cached in localStorage from an earlier session — just
// refresh the authoritative accounts list. ActiveAccountProvider then reconciles
// the active account to a real one. No toast, no snap-back; recovery is silent.
function handleAccountNotFound(): void {
  void queryClient.invalidateQueries({ queryKey: listAccountsKey() });
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (isAccountNotFound(error)) handleAccountNotFound();
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (isAccountNotFound(error)) handleAccountNotFound();
    },
  }),
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // 4xx are client-side problems — retrying won't help. In particular,
        // 404 "Account not found" should surface immediately so the global
        // error handler can clear the stale active account.
        if (
          error instanceof ApiError &&
          error.status >= 400 &&
          error.status < 500
        ) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

const router = createRouter({
  routeTree,
  context: {
    queryClient,
  },
  defaultPreload: "intent",
  // Since we're using React Query, we don't want loader calls to ever be stale
  // This will ensure that the loader is always called when the route is preloaded or visited
  defaultPreloadStaleTime: 0,
  scrollRestoration: true,
});

router.subscribe("onResolved", ({ toLocation }) => {
  trackPageView({ path: toLocation.pathname });
});

// Register things for typesafety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root")!;

if (!rootElement.innerHTML) {
  const root = createRoot(rootElement);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>,
  );
}
