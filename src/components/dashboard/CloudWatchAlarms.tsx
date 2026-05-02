import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, BellOff } from "lucide-react";
import { StatusIndicator } from "./StatusIndicator";

interface Alarm {
  name: string;
  metric: string;
  state: string;
  last_triggered: string;
}

function mapState(state: string): "healthy" | "unhealthy" | "warning" | "pending" {
  const s = state.toLowerCase();
  if (s === "ok") return "healthy";
  if (s === "alarm") return "unhealthy";
  if (s === "insufficient_data") return "pending";
  return "warning";
}

export const CloudWatchAlarms = () => {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlarms = () => {
      fetch("http://127.0.0.1:5000/api/alarms")
        .then((res) => res.json())
        .then((data) => setAlarms(data))
        .finally(() => setLoading(false));
    };
    fetchAlarms();
    const interval = setInterval(fetchAlarms, 30_000);
    return () => clearInterval(interval);
  }, []);

  // Only ALARM state counts as active — not INSUFFICIENT_DATA
  const activeAlarms = alarms.filter((a) => a.state.toUpperCase() === "ALARM").length;

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        {activeAlarms > 0 ? <Bell className="h-4 w-4 text-destructive" /> : <BellOff className="h-4 w-4 text-primary" />}
        <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground">CloudWatch Alarms</h2>
        {activeAlarms > 0 && (
          <span className="ml-2 rounded-full bg-destructive/20 px-2 py-0.5 text-[11px] font-mono font-medium text-destructive">
            {activeAlarms} active
          </span>
        )}
      </div>
      {loading ? (
        <p className="text-xs text-muted-foreground px-3 py-2">Loading...</p>
      ) : (
        <div className="space-y-1 max-h-[320px] overflow-y-auto pr-1">
          {alarms.map((alarm, i) => (
            <motion.div
              key={alarm.name}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.04 }}
              className="flex items-center gap-4 px-3 py-2.5 rounded-md bg-secondary/40 hover:bg-secondary/70 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-foreground truncate">{alarm.name}</div>
                <div className="text-[11px] font-mono text-muted-foreground">{alarm.metric}</div>
              </div>
              <div className="shrink-0">
                <StatusIndicator status={mapState(alarm.state)} />
              </div>
              <span className="text-[11px] font-mono text-muted-foreground w-20 text-right shrink-0">{alarm.last_triggered}</span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};
