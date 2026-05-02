import { motion } from "framer-motion";
import { Server, Cpu, HardDrive, Wifi } from "lucide-react";
import { StatusIndicator } from "./StatusIndicator";

type Status = "healthy" | "unhealthy" | "warning" | "pending";

type Instance = {
  name: string;
  instance_id: string;
  type: string;
  az: string;
  status: string;
  state: string;
  cpu: number;
  public_ip: string;
  launch_time: string | null;
};

type EC2StatusPanelProps = {
  instances: Instance[];
  isLoading: boolean;
  error: string | null;
};

const toStatus = (status: string): Status => {
  const normalized = status.toLowerCase();
  if (normalized === "healthy" || normalized === "unhealthy" || normalized === "warning" || normalized === "pending") {
    return normalized;
  }
  return "pending";
};

function formatUptime(launchTime: string | null, state: string): string {
  if (!launchTime || state !== "running") return "-";
  const launched = new Date(launchTime);
  const now = new Date();
  const diffMs = now.getTime() - launched.getTime();
  if (diffMs < 0) return "-";
  const totalSeconds = Math.floor(diffMs / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export const EC2StatusPanel = ({ instances, isLoading, error }: EC2StatusPanelProps) => (
  <div className="rounded-lg border border-border bg-card p-5">
    <div className="flex items-center gap-2 mb-4">
      <Server className="h-4 w-4 text-primary" />
      <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground">EC2 Instances</h2>
      <span className="ml-auto text-xs font-mono text-muted-foreground">{instances.length} total</span>
    </div>
    <div className="space-y-1">
      <div className="grid grid-cols-[1fr_100px_90px_90px_80px_80px] gap-2 px-3 py-1.5 text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
        <span>Instance</span><span>Type</span><span>AZ</span><span>Status</span><span>Uptime</span><span></span>
      </div>
      {isLoading && (
        <div className="px-3 py-4 text-xs font-mono text-muted-foreground">Loading instances...</div>
      )}
      {error && (
        <div className="px-3 py-4 text-xs font-mono text-destructive">{error}</div>
      )}
      {instances.map((inst, i) => (
        <motion.div
          key={inst.name}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className="grid grid-cols-[1fr_100px_90px_90px_80px_80px] gap-2 items-center px-3 py-2.5 rounded-md bg-secondary/40 hover:bg-secondary/70 transition-colors"
        >
          <div>
            <div className="text-sm font-medium text-foreground">{inst.name}</div>
            <div className="text-[11px] font-mono text-muted-foreground">{inst.cpu}% CPU</div>
          </div>
          <span className="text-xs font-mono text-secondary-foreground">{inst.type || "-"}</span>
          <span className="text-xs font-mono text-secondary-foreground">{inst.az ? inst.az.replace(/^[a-z]+-[a-z]+-\d+/, (m) => m.slice(-2).toUpperCase()) : "-"}</span>
          <StatusIndicator status={toStatus(inst.status)} />
          <span className="text-xs font-mono text-muted-foreground">{formatUptime(inst.launch_time, inst.state)}</span>
          <div className="flex gap-1.5 justify-end">
            <Cpu className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors" />
            <HardDrive className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors" />
            <Wifi className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors" />
          </div>
        </motion.div>
      ))}
    </div>
  </div>
);
