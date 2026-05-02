import { cn } from "@/lib/utils";

type Status = "healthy" | "unhealthy" | "warning" | "pending";

const statusConfig: Record<Status, { color: string; glow: string; label: string }> = {
  healthy: { color: "bg-success", glow: "glow-green", label: "Healthy" },
  unhealthy: { color: "bg-destructive", glow: "glow-red", label: "Unhealthy" },
  warning: { color: "bg-warning", glow: "glow-amber", label: "Warning" },
  pending: { color: "bg-muted-foreground", glow: "", label: "Pending" },
};

export const StatusIndicator = ({ status }: { status: Status }) => {
  const config = statusConfig[status];
  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn("h-2.5 w-2.5 rounded-full", config.color, config.glow)} />
      <span className={cn(
        "text-xs font-mono font-medium uppercase tracking-wider",
        status === "healthy" && "text-success",
        status === "unhealthy" && "text-destructive",
        status === "warning" && "text-warning",
        status === "pending" && "text-muted-foreground",
      )}>
        {config.label}
      </span>
    </span>
  );
};
