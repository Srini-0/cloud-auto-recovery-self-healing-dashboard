import { motion } from "framer-motion";
import { Server, AlertTriangle, CheckCircle2, Activity } from "lucide-react";

type Summary = {
  total_instances: number;
  healthy_instances: number;
  unhealthy_instances: number;
  avg_cpu: number;
};

type MetricCardsProps = {
  summary: Summary | null;
  isLoading: boolean;
};

export const MetricCards = ({ summary, isLoading }: MetricCardsProps) => {
  const metrics = [
    { label: "Total Instances", value: summary?.total_instances ?? 0, icon: Server },
    { label: "Healthy", value: summary?.healthy_instances ?? 0, icon: CheckCircle2, color: "text-success" },
    { label: "Unhealthy", value: summary?.unhealthy_instances ?? 0, icon: AlertTriangle, color: "text-destructive" },
    { label: "Avg CPU", value: summary ? `${summary.avg_cpu}%` : "0%", icon: Activity, color: "text-foreground" },
  ];

  return (
  <div className="grid grid-cols-4 gap-4">
    {metrics.map((m, i) => (
      <motion.div
        key={m.label}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: i * 0.08 }}
        className="rounded-lg border border-border bg-card p-4"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">{m.label}</span>
          <m.icon className={`h-4 w-4 ${m.color || "text-muted-foreground"}`} />
        </div>
        <span className={`text-2xl font-bold font-mono ${m.color || "text-foreground"}`}>
          {isLoading ? "..." : m.value}
        </span>
      </motion.div>
    ))}
  </div>
  );
};
