import { Suspense, useEffect, useRef, useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  getCartKey,
  useAddToCart,
  useGetProductSuspense,
  type ProductDetailOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { useActiveAccount } from "@/lib/active-account";
import { trackAddToCart, trackViewItem } from "@/lib/gtm";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { QuantityStepper } from "@/components/shop/quantity-stepper";

export const Route = createFileRoute("/product/$productId")({
  component: ProductDetailPage,
});

function ProductDetailPage() {
  const { productId } = Route.useParams();

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">← Catalog</Link>
        </Button>
      </div>

      <Suspense fallback={<DetailSkeleton />}>
        <ProductDetail productId={productId} />
      </Suspense>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="grid gap-8 md:grid-cols-2">
      <Skeleton className="aspect-[4/3] w-full" />
      <div className="space-y-4">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

function ProductDetail({ productId }: { productId: string }) {
  const { data: product } = useGetProductSuspense<ProductDetailOut>({
    params: { product_id: productId },
    ...selector<ProductDetailOut>(),
  });

  const { activeAccountId } = useActiveAccount();
  const queryClient = useQueryClient();
  const [quantity, setQuantity] = useState(1);
  const lastViewedKey = useRef<string | null>(null);

  useEffect(() => {
    const viewedKey = `${product.id}:${activeAccountId ?? "anonymous"}`;
    if (lastViewedKey.current === viewedKey) return;
    lastViewedKey.current = viewedKey;
    trackViewItem({ product, account_id: activeAccountId });
  }, [activeAccountId, product]);

  const addMutation = useAddToCart({
    mutation: {
      onSuccess: (response, variables) => {
        const qty = variables.data.quantity ?? 1;
        trackAddToCart({
          product,
          quantity: qty,
          cart_id: response.data.cart_id,
          account_id: activeAccountId,
        });
        toast.success(`Added ${qty} × "${product.name}" to cart`);
        setQuantity(1);
        if (activeAccountId) {
          queryClient.invalidateQueries({
            queryKey: getCartKey({ account_id: activeAccountId }),
          });
        }
      },
      onError: (e) => toast.error(e.message ?? "Failed to add to cart"),
    },
  });

  const handleAdd = () => {
    if (!activeAccountId) {
      toast.error("No active account selected");
      return;
    }
    addMutation.mutate({
      params: { account_id: activeAccountId },
      data: { product_id: product.id, quantity },
    });
  };

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <div className="rounded-lg border bg-muted overflow-hidden">
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full max-h-[480px] object-contain bg-white p-4"
        />
      </div>

      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{product.name}</h1>
          <p className="mt-1 text-muted-foreground">{product.description}</p>
        </div>

        <p className="text-4xl font-semibold">
          €{product.price_eur.toFixed(2)}
        </p>

        {product.long_description && (
          <p className="leading-relaxed text-sm">
            {product.long_description}
          </p>
        )}

        <Card>
          <CardContent className="flex items-center justify-between gap-4 py-4">
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Quantity</span>
              <QuantityStepper
                value={quantity}
                onChange={setQuantity}
                disabled={addMutation.isPending}
              />
            </div>
            <Button
              size="lg"
              onClick={handleAdd}
              disabled={!activeAccountId || addMutation.isPending}
            >
              {addMutation.isPending ? "Adding..." : "Add to cart"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
