import { Suspense, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

import {
  listAccountsKey,
  useCreateAccount,
  useDeleteAccount,
  useListAccountsSuspense,
  type AccountIn,
  type AccountOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { useActiveAccount } from "@/lib/active-account";
import { trackAccountDeleted, trackSignUp } from "@/lib/gtm";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/accounts")({
  component: AccountsPage,
});

function AccountsPage() {
  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold">Accounts</h1>
          <p className="text-muted-foreground">All registered shop accounts</p>
        </div>
        <CreateAccountDialog />
      </header>

      <Suspense fallback={<Skeleton className="h-64 w-full" />}>
        <AccountsTable />
      </Suspense>
    </div>
  );
}

function AccountsTable() {
  const { data: accounts } = useListAccountsSuspense<AccountOut[]>(
    selector<AccountOut[]>(),
  );
  const { activeAccountId } = useActiveAccount();

  if (accounts.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          No accounts yet. Create one to get started.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {accounts.length} account{accounts.length === 1 ? "" : "s"}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Street</TableHead>
              <TableHead>No.</TableHead>
              <TableHead>Postcode</TableHead>
              <TableHead>City</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Date of birth</TableHead>
              <TableHead className="w-[140px] text-right" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((a) => (
              <TableRow key={a.id}>
                <TableCell className="font-medium">
                  {a.first_name} {a.surname}
                </TableCell>
                <TableCell>{a.email}</TableCell>
                <TableCell
                  className="max-w-[200px] truncate"
                  title={a.street}
                >
                  {a.street}
                </TableCell>
                <TableCell className="tabular-nums">{a.house_number}</TableCell>
                <TableCell className="tabular-nums">{a.postal_code}</TableCell>
                <TableCell>{a.city}</TableCell>
                <TableCell>{a.country}</TableCell>
                <TableCell>{a.date_of_birth}</TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    {a.id === activeAccountId && (
                      <Badge variant="secondary">Active</Badge>
                    )}
                    <DeleteAccountButton
                      account={a}
                      isOnly={accounts.length <= 1}
                      isActive={a.id === activeAccountId}
                    />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function DeleteAccountButton({
  account,
  isOnly,
  isActive,
}: {
  account: AccountOut;
  isOnly: boolean;
  isActive: boolean;
}) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const blockedReason = isOnly
    ? "Cannot delete the last remaining account"
    : isActive
      ? "Cannot delete the active account — switch first"
      : null;

  const mutation = useDeleteAccount({
    mutation: {
      onSuccess: () => {
        trackAccountDeleted({ account });
        toast.success(`Deleted account "${account.first_name} ${account.surname}"`);
        queryClient.invalidateQueries({ queryKey: listAccountsKey() });
        setOpen(false);
      },
      onError: (e) => toast.error(e.message ?? "Failed to delete account"),
    },
  });

  if (blockedReason) {
    return (
      <Button
        variant="ghost"
        size="icon"
        disabled
        title={blockedReason}
        aria-label={blockedReason}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Delete account ${account.first_name} ${account.surname}`}
          title="Delete account"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Delete account {account.first_name} {account.surname}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes the account and any items in its cart.
            Accounts that already have purchases cannot be deleted.
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
              mutation.mutate({ params: { account_id: account.id } });
            }}
          >
            {mutation.isPending ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

const EMPTY_FORM: AccountIn = {
  first_name: "",
  surname: "",
  street: "",
  house_number: "",
  postal_code: "",
  city: "",
  country: "",
  date_of_birth: "" as unknown as AccountIn["date_of_birth"],
  email: "",
};

function CreateAccountDialog() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<AccountIn>(EMPTY_FORM);
  const queryClient = useQueryClient();

  const mutation = useCreateAccount({
    mutation: {
      onSuccess: (response) => {
        trackSignUp({ account: response.data });
        toast.success(`Account "${form.first_name} ${form.surname}" created`);
        queryClient.invalidateQueries({ queryKey: listAccountsKey() });
        setOpen(false);
        setForm(EMPTY_FORM);
      },
      onError: (e) => toast.error(e.message ?? "Failed to create account"),
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>New account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create account</DialogTitle>
          <DialogDescription>
            Fill in the customer details below.
          </DialogDescription>
        </DialogHeader>

        <form
          className="grid gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(form);
          }}
        >
          <div className="grid grid-cols-2 gap-4">
            <Field label="First name">
              <Input
                required
                value={form.first_name}
                onChange={(e) =>
                  setForm({ ...form, first_name: e.target.value })
                }
              />
            </Field>
            <Field label="Surname">
              <Input
                required
                value={form.surname}
                onChange={(e) =>
                  setForm({ ...form, surname: e.target.value })
                }
              />
            </Field>
          </div>
          <Field label="Email">
            <Input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Field>
          <Field label="Street">
            <Input
              required
              value={form.street}
              onChange={(e) => setForm({ ...form, street: e.target.value })}
            />
          </Field>
          <div className="grid grid-cols-3 gap-4">
            <Field label="Number">
              <Input
                required
                value={form.house_number}
                onChange={(e) =>
                  setForm({ ...form, house_number: e.target.value })
                }
              />
            </Field>
            <Field label="Post code">
              <Input
                required
                value={form.postal_code}
                onChange={(e) =>
                  setForm({ ...form, postal_code: e.target.value })
                }
              />
            </Field>
            <Field label="City">
              <Input
                required
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Country">
              <Input
                required
                value={form.country}
                onChange={(e) =>
                  setForm({ ...form, country: e.target.value })
                }
              />
            </Field>
            <Field label="Date of birth">
              <Input
                type="date"
                required
                value={form.date_of_birth as unknown as string}
                onChange={(e) =>
                  setForm({
                    ...form,
                    date_of_birth: e.target
                      .value as unknown as AccountIn["date_of_birth"],
                  })
                }
              />
            </Field>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
