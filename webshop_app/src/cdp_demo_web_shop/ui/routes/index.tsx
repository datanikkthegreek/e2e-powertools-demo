import { Suspense, useEffect, useMemo, useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Search, X } from "lucide-react";

import {
  getCartKey,
  useAddToCart,
  useListProductsSuspense,
  type ProductOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { useActiveAccount } from "@/lib/active-account";
import { trackAddToCart } from "@/lib/gtm";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { QuantityStepper } from "@/components/shop/quantity-stepper";

export const Route = createFileRoute("/")({
  component: CatalogPage,
});

function CatalogPage() {
  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold">Catalog</h1>
          <p className="text-muted-foreground">
            Browse our selection of Bosch power tools
          </p>
        </div>
      </header>

      <Suspense fallback={<CatalogSkeleton />}>
        <Catalog />
      </Suspense>
    </div>
  );
}

function CatalogSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} className="h-[360px] w-full" />
      ))}
    </div>
  );
}

function Catalog() {
  const { data: products } = useListProductsSuspense<ProductOut[]>(
    selector<ProductOut[]>(),
  );

  const [minPrice, maxPrice] = useMemo<[number, number]>(() => {
    if (products.length === 0) return [0, 0];
    const prices = products.map((p) => p.price_eur);
    return [Math.floor(Math.min(...prices)), Math.ceil(Math.max(...prices))];
  }, [products]);

  const [search, setSearch] = useState("");
  const [range, setRange] = useState<[number, number]>([minPrice, maxPrice]);

  useEffect(() => {
    setRange([minPrice, maxPrice]);
  }, [minPrice, maxPrice]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return products.filter(
      (p) =>
        (q === "" || p.name.toLowerCase().includes(q)) &&
        p.price_eur >= range[0] &&
        p.price_eur <= range[1],
    );
  }, [products, search, range]);

  const isFiltered =
    search.trim() !== "" || range[0] !== minPrice || range[1] !== maxPrice;

  const handleReset = () => {
    setSearch("");
    setRange([minPrice, maxPrice]);
  };

  return (
    <div className="space-y-4">
      <CatalogToolbar
        search={search}
        onSearch={setSearch}
        range={range}
        onRangeChange={setRange}
        minPrice={minPrice}
        maxPrice={maxPrice}
        isFiltered={isFiltered}
        onReset={handleReset}
        totalCount={products.length}
        visibleCount={filtered.length}
      />

      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground space-y-3">
            <p>No products match your filters.</p>
            {isFiltered && (
              <Button variant="outline" size="sm" onClick={handleReset}>
                Reset filters
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {filtered.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}

interface CatalogToolbarProps {
  search: string;
  onSearch: (value: string) => void;
  range: [number, number];
  onRangeChange: (value: [number, number]) => void;
  minPrice: number;
  maxPrice: number;
  isFiltered: boolean;
  onReset: () => void;
  totalCount: number;
  visibleCount: number;
}

function CatalogToolbar({
  search,
  onSearch,
  range,
  onRangeChange,
  minPrice,
  maxPrice,
  isFiltered,
  onReset,
  totalCount,
  visibleCount,
}: CatalogToolbarProps) {
  const sliderDisabled = minPrice === maxPrice;

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-4 lg:flex-row lg:items-end lg:gap-6">
        <div className="flex-1 max-w-sm">
          <label className="text-xs font-medium text-muted-foreground mb-1 block">
            Search
          </label>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              type="search"
              placeholder="Search by name (e.g. GBH, drill)"
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>

        <div className="flex-1 max-w-md">
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-muted-foreground">
              Price
            </label>
            <span className="text-xs tabular-nums text-muted-foreground">
              €{range[0]} – €{range[1]}
            </span>
          </div>
          <Slider
            min={minPrice}
            max={maxPrice}
            step={10}
            value={range}
            onValueChange={(v) => onRangeChange([v[0], v[1]] as [number, number])}
            disabled={sliderDisabled}
            className="py-2"
          />
        </div>

        <div className="flex items-center gap-3 lg:ml-auto">
          <span className="text-xs text-muted-foreground tabular-nums">
            Showing {visibleCount} of {totalCount}
          </span>
          {isFiltered && (
            <Button variant="ghost" size="sm" onClick={onReset}>
              <X className="h-4 w-4 mr-1" />
              Reset
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ProductCard({ product }: { product: ProductOut }) {
  const { activeAccountId } = useActiveAccount();
  const queryClient = useQueryClient();
  const [quantity, setQuantity] = useState(1);

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
        toast.success(
          `Added ${qty} × "${product.name}" to cart`,
        );
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
    <Card className="flex flex-col overflow-hidden">
      <div className="aspect-[4/3] w-full bg-muted">
        <img
          src={product.image_url}
          alt={product.name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      </div>
      <CardHeader>
        <CardTitle className="text-base">{product.name}</CardTitle>
        <CardDescription className="line-clamp-2">
          {product.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <p className="text-2xl font-semibold">
          €{product.price_eur.toFixed(2)}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Quantity</span>
          <QuantityStepper
            value={quantity}
            onChange={setQuantity}
            size="sm"
            disabled={addMutation.isPending}
          />
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button
          size="sm"
          className="flex-1"
          onClick={handleAdd}
          disabled={!activeAccountId || addMutation.isPending}
        >
          {addMutation.isPending ? "Adding..." : "Add to cart"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="flex-1"
          asChild
        >
          <Link
            to="/product/$productId"
            params={{ productId: product.id }}
          >
            More info
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
