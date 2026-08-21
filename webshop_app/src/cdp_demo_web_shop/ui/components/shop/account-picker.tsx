import { Suspense, useCallback, useRef } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useListAccountsSuspense, type AccountOut } from "@/lib/api";
import { selector } from "@/lib/selector";
import { useActiveAccount } from "@/lib/active-account";
import { trackAccountSelected } from "@/lib/gtm";

function AccountPickerInner() {
  const { activeAccountId, setActiveAccountId } = useActiveAccount();
  const lastTrackedSelection = useRef<string | null>(null);
  const { data: accounts } = useListAccountsSuspense<AccountOut[]>(
    selector<AccountOut[]>(),
  );

  // Manual selection only. Auto-selecting a valid account when the stored id is
  // missing/stale is handled centrally in ActiveAccountProvider, so the picker
  // never competes with that reconciliation.
  const handleSelect = useCallback(
    (accountId: string) => {
      setActiveAccountId(accountId);
      if (lastTrackedSelection.current === accountId) return;
      lastTrackedSelection.current = accountId;
      trackAccountSelected({ account_id: accountId, source: "manual" });
    },
    [setActiveAccountId],
  );

  if (accounts.length === 0) {
    return (
      <span className="text-xs text-muted-foreground">No accounts yet</span>
    );
  }

  return (
    <Select value={activeAccountId ?? ""} onValueChange={handleSelect}>
      <SelectTrigger className="w-[260px]">
        <SelectValue placeholder="Select account" />
      </SelectTrigger>
      <SelectContent>
        {accounts.map((a) => (
          <SelectItem key={a.id} value={a.id}>
            {a.first_name} {a.surname}{" "}
            <span className="text-muted-foreground">({a.email})</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function AccountPicker() {
  return (
    <Suspense fallback={<Skeleton className="h-9 w-[260px]" />}>
      <AccountPickerInner />
    </Suspense>
  );
}

export default AccountPicker;
