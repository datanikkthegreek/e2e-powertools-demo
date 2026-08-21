import { ThemeProvider } from "@/components/apx/theme-provider";
import { ShopNavbar } from "@/components/shop/shop-navbar";
import { ActiveAccountProvider } from "@/lib/active-account";
import { QueryClient } from "@tanstack/react-query";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { Suspense } from "react";
import { Toaster } from "sonner";

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  component: () => (
    <ThemeProvider defaultTheme="dark" storageKey="apx-ui-theme">
      <ActiveAccountProvider>
        <div className="min-h-screen flex flex-col bg-background">
          <ShopNavbar />
          <main className="flex-1">
            <Suspense fallback={null}>
              <Outlet />
            </Suspense>
          </main>
        </div>
        <Toaster richColors />
      </ActiveAccountProvider>
    </ThemeProvider>
  ),
});
