import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  getCartKey,
  listPurchasesKey,
  useCheckout,
  useClearCart,
  useGetCart,
  useRemoveCartItem,
  useUpdateCartItem,
  type CartItemOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { useActiveAccount } from "@/lib/active-account";
import {
  trackAbandonCart,
  trackCartQuantityChange,
  trackPurchase,
} from "@/lib/gtm";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/cart")({
  component: CartPage,
});

function CartPage() {
  const { activeAccountId } = useActiveAccount();

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Shopping Cart</h1>
        <p className="text-muted-foreground">
          Review your selection and complete the purchase
        </p>
      </header>

      {!activeAccountId ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            Select an account in the top bar to view its cart.
          </CardContent>
        </Card>
      ) : (
        <CartView accountId={activeAccountId} />
      )}
    </div>
  );
}

function CartView({ accountId }: { accountId: string }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const {
    data: items,
    isPending,
    isError,
  } = useGetCart<CartItemOut[]>({
    params: { account_id: accountId },
    ...selector<CartItemOut[]>(),
  });

  const invalidateCart = () =>
    queryClient.invalidateQueries({
      queryKey: getCartKey({ account_id: accountId }),
    });

  const updateMutation = useUpdateCartItem({
    mutation: {
      onSuccess: (response) => {
        const previousItem = items?.find(
          (item) => item.product_id === response.data.product_id,
        );
        if (previousItem) {
          trackCartQuantityChange({
            item: previousItem,
            previous_quantity: previousItem.quantity,
            new_quantity: response.data.quantity,
            account_id: accountId,
          });
        }
        invalidateCart();
      },
      onError: (e) => toast.error(e.message ?? "Failed to update item"),
    },
  });

  const removeMutation = useRemoveCartItem({
    mutation: {
      onSuccess: (_, variables) => {
        const removedItem = items?.find(
          (item) => item.product_id === variables.params.product_id,
        );
        if (removedItem) {
          trackCartQuantityChange({
            item: removedItem,
            previous_quantity: removedItem.quantity,
            new_quantity: 0,
            account_id: accountId,
            cart_action: "remove_item",
          });
        }
        invalidateCart();
        toast.success("Item removed");
      },
      onError: (e) => toast.error(e.message ?? "Failed to remove item"),
    },
  });

  const checkoutMutation = useCheckout({
    mutation: {
      onSuccess: (response) => {
        trackPurchase({ purchase: response.data, account_id: accountId });
        toast.success("Purchase complete");
        invalidateCart();
        queryClient.invalidateQueries({ queryKey: listPurchasesKey() });
        navigate({ to: "/purchases" });
      },
      onError: (e) => toast.error(e.message ?? "Checkout failed"),
    },
  });

  const abandonMutation = useClearCart({
    mutation: {
      onSuccess: () => {
        trackAbandonCart({ items: items ?? [], account_id: accountId });
        toast.info("Cart abandoned");
        invalidateCart();
        navigate({ to: "/" });
      },
      onError: (e) => toast.error(e.message ?? "Failed to abandon cart"),
    },
  });

  if (isPending) {
    return <Skeleton className="h-64 w-full" />;
  }

  // On error (e.g. a transient stale-account 404), the global QueryCache
  // handler in main.tsx refreshes the accounts list and ActiveAccountProvider
  // reconciles to a valid account; render nothing while that re-render settles.
  if (isError || !items) {
    return null;
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          Your cart is empty. Add some tools from the catalog.
        </CardContent>
      </Card>
    );
  }

  const total = items.reduce(
    (acc: number, i: CartItemOut) => acc + i.line_total_eur,
    0,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {items.length} item{items.length === 1 ? "" : "s"}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Product</TableHead>
              <TableHead className="text-right">Unit price</TableHead>
              <TableHead className="w-[180px] text-center">Quantity</TableHead>
              <TableHead className="text-right">Line total</TableHead>
              <TableHead className="w-[80px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item: CartItemOut) => (
              <TableRow key={item.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="h-10 w-14 rounded object-cover"
                      loading="lazy"
                    />
                    <div>
                      <div className="font-medium">{item.product.name}</div>
                      <div className="text-xs text-muted-foreground line-clamp-1">
                        {item.product.description}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  €{item.product.price_eur.toFixed(2)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={item.quantity <= 1 || updateMutation.isPending}
                      onClick={() =>
                        updateMutation.mutate({
                          params: {
                            account_id: accountId,
                            product_id: item.product_id,
                          },
                          data: { quantity: item.quantity - 1 },
                        })
                      }
                    >
                      −
                    </Button>
                    <span className="w-8 text-center">{item.quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={updateMutation.isPending}
                      onClick={() =>
                        updateMutation.mutate({
                          params: {
                            account_id: accountId,
                            product_id: item.product_id,
                          },
                          data: { quantity: item.quantity + 1 },
                        })
                      }
                    >
                      +
                    </Button>
                  </div>
                </TableCell>
                <TableCell className="text-right font-medium">
                  €{item.line_total_eur.toFixed(2)}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={removeMutation.isPending}
                    onClick={() =>
                      removeMutation.mutate({
                        params: {
                          account_id: accountId,
                          product_id: item.product_id,
                        },
                      })
                    }
                  >
                    Remove
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
      <CardFooter className="flex items-center justify-between border-t">
        <div className="text-lg">
          Total: <span className="font-semibold">€{total.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="lg"
            className="border-2 border-red-500 text-red-600 hover:bg-red-50 hover:text-red-700"
            disabled={abandonMutation.isPending || checkoutMutation.isPending}
            onClick={() =>
              abandonMutation.mutate({ params: { account_id: accountId } })
            }
          >
            {abandonMutation.isPending ? "Abandoning..." : "Abandon"}
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-2 border-green-600 text-green-700 hover:bg-green-50 hover:text-green-800"
            disabled={checkoutMutation.isPending || abandonMutation.isPending}
            onClick={() =>
              checkoutMutation.mutate({ params: { account_id: accountId } })
            }
          >
            {checkoutMutation.isPending ? "Processing..." : "Purchase"}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
