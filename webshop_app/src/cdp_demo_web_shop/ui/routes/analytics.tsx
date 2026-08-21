import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Activity,
  Eye,
  Play,
  RefreshCw,
  ShoppingBag,
  ShoppingCart,
  UserPlus,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  useAnalyticsOverview,
  useGetTriggeredPipelineRun,
  useRunTriggeredPipeline,
  useTablePreview,
  type AnalyticsOut,
  type PipelineRunStatusOut,
  type TablePreviewOut,
} from "@/lib/api";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/analytics")({
  component: AnalyticsPage,
});

interface Metric {
  key: keyof AnalyticsOut;
  label: string;
  description: string;
  icon: LucideIcon;
}

const METRICS: Metric[] = [
  {
    key: "total_events",
    label: "Total Events",
    description: "All tracking events captured",
    icon: Activity,
  },
  {
    key: "page_views",
    label: "Page Views",
    description: "page_view events",
    icon: Eye,
  },
  {
    key: "registrations",
    label: "Registrations",
    description: "Sign-up events",
    icon: UserPlus,
  },
  {
    key: "purchases",
    label: "Purchases",
    description: "Completed checkouts",
    icon: ShoppingBag,
  },
  {
    key: "abandoned_carts",
    label: "Abandoned Carts",
    description: "Carts left without checkout",
    icon: ShoppingCart,
  },
];

interface TablePreviewConfig {
  key: string;
  label: string;
  description: string;
}

const TABLE_PREVIEWS: TablePreviewConfig[] = [
  {
    key: "event_sign_up",
    label: "event_sign_up",
    description: "Silver: sign-up events",
  },
  {
    key: "event_purchase",
    label: "event_purchase",
    description: "Silver: purchase events",
  },
  {
    key: "gold_customer_360",
    label: "gold_customer_360",
    description: "Gold: one row per customer (Customer 360 feature table)",
  },
];

function AnalyticsPage() {
  const queryClient = useQueryClient();
  const [ran, setRan] = useState(false);
  const pipeline = usePipelineRunner();

  // Run on demand only (enabled: false) so the warehouse isn't hit on mount.
  const { data, error, isFetching, isFetched, refetch } =
    useAnalyticsOverview<AnalyticsOut>({
      query: { enabled: false, select: (d) => d.data },
    });

  const handleRefresh = () => {
    setRan(true);
    void refetch();
    // Re-run any already-enabled table previews. On the first click they
    // enable + auto-fetch via `ran`; on subsequent clicks this refetches them.
    void queryClient.refetchQueries({
      predicate: (q) =>
        typeof q.queryKey[0] === "string" &&
        (q.queryKey[0] as string).startsWith("/api/analytics/tables"),
    });
  };

  const metrics = data;

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Real-time metrics queried live from the SQL Warehouse
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={pipeline.run}
            disabled={pipeline.isRunning || pipeline.isStarting}
          >
            <Play className="h-4 w-4 mr-2" />
            {pipeline.isStarting
              ? "Starting..."
              : pipeline.isRunning
                ? "Running..."
                : "Run Triggered Pipeline"}
          </Button>
          <Button onClick={handleRefresh} disabled={isFetching}>
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isFetching ? "animate-spin" : ""}`}
            />
            {isFetching ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </header>

      {pipeline.panel}

      {error && (
        <Card>
          <CardContent className="py-4 text-sm text-destructive">
            Failed to load analytics: {error.message}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {METRICS.map((metric) => {
          const Icon = metric.icon;
          const value = metrics?.[metric.key];
          return (
            <Card key={metric.key}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {metric.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold tabular-nums">
                  {value !== undefined
                    ? value.toLocaleString()
                    : isFetched
                      ? "0"
                      : "—"}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {metric.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="space-y-6">
        <h2 className="text-xl font-semibold">Tables</h2>
        {TABLE_PREVIEWS.map((table) => (
          <TablePreviewCard key={table.key} config={table} enabled={ran} />
        ))}
      </div>

      {!ran && !isFetching && (
        <p className="text-sm text-muted-foreground">
          Click <span className="font-medium">Refresh</span> to run the queries.
        </p>
      )}
    </div>
  );
}

function formatElapsed(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

// Life-cycle states are surfaced to the user as friendly labels.
const LIFE_CYCLE_LABELS: Record<string, string> = {
  PENDING: "Pending",
  QUEUED: "Queued",
  RUNNING: "Running",
  TERMINATING: "Finishing",
  TERMINATED: "Finished",
  SKIPPED: "Skipped",
  INTERNAL_ERROR: "Error",
  BLOCKED: "Blocked",
  WAITING_FOR_RETRY: "Retrying",
};

function usePipelineRunner() {
  const [runId, setRunId] = useState<number | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [finished, setFinished] = useState(false);

  const runMutation = useRunTriggeredPipeline({
    mutation: {
      onSuccess: (response) => {
        setRunId(response.data.run_id);
        setStartedAt(Date.now());
        setElapsed(0);
        setFinished(false);
      },
      onError: (e) => toast.error(e.message ?? "Failed to start pipeline"),
    },
  });

  const isRunning = runId !== null && !finished;

  const statusQuery = useGetTriggeredPipelineRun<{ data: PipelineRunStatusOut }>(
    {
      params: { run_id: runId ?? 0 },
      query: {
        enabled: isRunning,
        refetchInterval: isRunning ? 3000 : false,
      },
    },
  );

  const status = statusQuery.data?.data;

  // Tick the elapsed timer once per second while the run is in flight.
  useEffect(() => {
    if (startedAt === null || finished) return;
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [startedAt, finished]);

  // Detect a terminal run state, freeze the timer, and report the result.
  useEffect(() => {
    if (!status || finished || !status.finished) return;
    setFinished(true);
    const finalSeconds =
      startedAt !== null ? Math.floor((Date.now() - startedAt) / 1000) : elapsed;
    setElapsed(finalSeconds);
    if (status.result_state === "SUCCESS") {
      toast.success(`Pipeline completed in ${formatElapsed(finalSeconds)}`);
    } else {
      toast.error(
        `Pipeline run ${status.result_state ?? status.life_cycle_state ?? "failed"}`,
      );
    }
  }, [status, finished, startedAt, elapsed]);

  const run = () => {
    if (isRunning || runMutation.isPending) return;
    runMutation.mutate();
  };

  const lifeCycle = status?.life_cycle_state ?? null;
  const stateLabel = finished
    ? (status?.result_state ?? "Finished")
    : lifeCycle
      ? (LIFE_CYCLE_LABELS[lifeCycle] ?? lifeCycle)
      : "Starting";

  const panel =
    runId === null ? null : (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            cdp-triggered-pipeline run
          </CardTitle>
          <span className="text-sm font-mono tabular-nums text-muted-foreground">
            {formatElapsed(elapsed)}
          </span>
        </CardHeader>
        <CardContent className="space-y-2">
          <Progress value={finished ? 100 : undefined} indeterminate={!finished} />
          <p className="text-xs text-muted-foreground">
            Run #{runId} · {stateLabel}
          </p>
        </CardContent>
      </Card>
    );

  return { run, isRunning, isStarting: runMutation.isPending && !runId, panel };
}

function TablePreviewCard({
  config,
  enabled,
}: {
  config: TablePreviewConfig;
  enabled: boolean;
}) {
  const { data, error, isFetching } = useTablePreview<TablePreviewOut>({
    params: { table_key: config.key },
    query: { enabled, select: (d) => d.data },
  });

  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardTitle className="text-base font-mono">{config.label}</CardTitle>
        <p className="text-xs text-muted-foreground">
          {config.description}
          {data ? ` · ${data.fqn}` : ""}
        </p>
      </CardHeader>
      <CardContent>
        {!enabled && (
          <p className="text-sm text-muted-foreground">
            Click <span className="font-medium">Refresh</span> to load.
          </p>
        )}

        {enabled && isFetching && !data && (
          <Skeleton className="h-40 w-full" />
        )}

        {error && (
          <p className="text-sm text-destructive">
            Failed to load: {error.message}
          </p>
        )}

        {data &&
          (data.rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No rows.</p>
          ) : (
            <>
              <div className="overflow-x-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {data.columns.map((column) => (
                        <TableHead key={column} className="whitespace-nowrap">
                          {column}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.rows.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                          <TableCell
                            key={cellIndex}
                            className="whitespace-nowrap max-w-[320px] truncate"
                            title={cell ?? undefined}
                          >
                            {cell ?? (
                              <span className="text-muted-foreground italic">
                                null
                              </span>
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Showing {data.rows.length} row
                {data.rows.length === 1 ? "" : "s"}
                {data.truncated ? ` (capped at ${data.row_limit})` : ""}.
              </p>
            </>
          ))}
      </CardContent>
    </Card>
  );
}
