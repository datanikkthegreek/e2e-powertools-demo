import { Suspense, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

import {
  listPurchasesKey,
  useDeletePurchase,
  useListPurchasesSuspense,
  type PurchaseOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { trackPurchaseDeleted } from "@/lib/gtm";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/purchases")({
  component: PurchasesPage,
});

function PurchasesPage() {
  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Purchases</h1>
        <p className="text-muted-foreground">
          Order history across all accounts
        </p>
      </header>

      <Suspense fallback={<Skeleton className="h-64 w-full" />}>
        <PurchasesList />
      </Suspense>
    </div>
  );
}

function PurchasesList() {
  const { data: purchases } = useListPurchasesSuspense<PurchaseOut[]>(
    selector<PurchaseOut[]>(),
  );

  if (purchases.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          No purchases yet. Add items to your cart and check out.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {purchases.map((p) => (
        <PurchaseCard key={p.id} purchase={p} />
      ))}
    </div>
  );
}

function PurchaseCard({ purchase }: { purchase: PurchaseOut }) {
  const created = new Date(purchase.created_at);
  const itemCount = purchase.lines.reduce((acc, l) => acc + l.quantity, 0);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="text-base font-semibold">
            {purchase.account_name}{" "}
            <span className="font-normal text-muted-foreground">
              ({purchase.account_email})
            </span>
          </CardTitle>
          <CardDescription>
            {created.toLocaleString()} · {itemCount} item
            {itemCount === 1 ? "" : "s"}
          </CardDescription>
        </div>
        <div className="flex items-start gap-3">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Total</div>
            <div className="text-2xl font-semibold">
              €{purchase.total_eur.toFixed(2)}
            </div>
          </div>
          <DeletePurchaseButton purchase={purchase} />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tool</TableHead>
              <TableHead className="text-right">Unit price</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Line total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {purchase.lines.map((line) => (
              <TableRow key={line.id}>
                <TableCell className="font-medium">
                  {line.name_snapshot}
                </TableCell>
                <TableCell className="text-right">
                  €{line.unit_price_eur.toFixed(2)}
                </TableCell>
                <TableCell className="text-right">{line.quantity}</TableCell>
                <TableCell className="text-right font-medium">
                  €{line.line_total_eur.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function DeletePurchaseButton({ purchase }: { purchase: PurchaseOut }) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const mutation = useDeletePurchase({
    mutation: {
      onSuccess: () => {
        trackPurchaseDeleted({ purchase });
        toast.success("Purchase deleted");
        queryClient.invalidateQueries({ queryKey: listPurchasesKey() });
        setOpen(false);
      },
      onError: (e) => toast.error(e.message ?? "Failed to delete purchase"),
    },
  });

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Delete purchase"
          title="Delete purchase"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this purchase?</AlertDialogTitle>
          <AlertDialogDescription>
            Order history for {purchase.account_name} from{" "}
            {new Date(purchase.created_at).toLocaleString()} will be permanently
            removed.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={mutation.isPending}
            onClick={(e) => {
              e.preventDefault();
              mutation.mutate({ params: { purchase_id: purchase.id } });
            }}
          >
            {mutation.isPending ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
