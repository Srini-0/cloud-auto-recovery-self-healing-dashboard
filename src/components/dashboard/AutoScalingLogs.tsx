import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpCircle, ArrowDownCircle, RefreshCw, Scaling } from "lucide-react";

interface ScalingLog {
  time: string;
  action: string;
  description: string;
}

function getIconAndColor(action: string) {
  const a = action.toLowerCase();
  if (a === "terminate") return { Icon: ArrowDownCircle, color: "text-warning" };
  if (a === "healthcheck") return { Icon: RefreshCw, color: "text-destructive" };
  return { Icon: ArrowUpCircle, color: "text-success" };
}

export const AutoScalingLogs = () => {
  const [logs, setLogs] = useState<ScalingLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = () => {
      fetch("http://127.0.0.1:5000/api/scaling")
        .then((res) => res.json())
        .then((data) => setLogs(data))
        .finally(() => setLoading(false));
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Scaling className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground">Auto Scaling Activity</h2>
      </div>
      {loading ? (
        <p className="text-xs text-muted-foreground px-3 py-2">Loading...</p>
      ) : (
        <div className="space-y-0.5 max-h-[320px] overflow-y-auto pr-1">
          {logs.map((log, i) => {
            const { Icon, color } = getIconAndColor(log.action);
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-start gap-3 px-3 py-2.5 rounded-md hover:bg-secondary/40 transition-colors"
              >
                <span className="text-[11px] font-mono text-muted-foreground pt-0.5 w-16 shrink-0">{log.time}</span>
                <Icon className={`h-4 w-4 shrink-0 mt-0.5 ${color}`} />
                <div className="min-w-0">
                  <span className="text-xs font-semibold text-foreground">{log.action}</span>
                  <p className="text-[11px] font-mono text-muted-foreground leading-relaxed">{log.description}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};
