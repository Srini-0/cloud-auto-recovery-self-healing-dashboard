import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, AlertTriangle, Skull, Search, Activity, Wrench, CheckCircle2, RefreshCw, Play, Eye } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface RecoveryEvent {
  type: string;
  status: string;
  message: string;
  time: string;
  instance_id: string;
  failure_reason: string | null;
  fix_applied: string | null;
  failure_type: string | null;
  action_taken: string | null;
  result: string | null;
  cpu_at_failure: number | null;
}

interface RecoveryResponse {
  events: RecoveryEvent[];
  total_recoveries: number;
  last_recovery_time: string | null;
}

// ─── Config maps ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { bg: string; text: string; border: string; label: string }> = {
  HEALTHY:    { bg: "bg-[#00d4aa]/15",  text: "text-[#00d4aa]",  border: "border-l-[#00d4aa]",  label: "HEALTHY" },
  COMPLETED:  { bg: "bg-[#00d4aa]/15",  text: "text-[#00d4aa]",  border: "border-l-[#00d4aa]",  label: "COMPLETED" },
  RECOVERING: { bg: "bg-[#ffaa00]/15",  text: "text-[#ffaa00]",  border: "border-l-[#ffaa00]",  label: "RECOVERING" },
  "IN-PROGRESS": { bg: "bg-[#ffaa00]/15", text: "text-[#ffaa00]", border: "border-l-[#ffaa00]", label: "IN-PROGRESS" },
  TRIGGERED:  { bg: "bg-[#ff4444]/15",  text: "text-[#ff4444]",  border: "border-l-[#ff4444]",  label: "TRIGGERED" },
  FAILED:     { bg: "bg-[#ff4444]/15",  text: "text-[#ff4444]",  border: "border-l-[#ff4444]",  label: "FAILED" },
  MONITORING: { bg: "bg-[#0088ff]/15",  text: "text-[#0088ff]",  border: "border-l-[#0088ff]",  label: "MONITORING" },
};

const DEFAULT_STATUS = { bg: "bg-muted/20", text: "text-muted-foreground", border: "border-l-border", label: "UNKNOWN" };

function getStatus(s: string) {
  return STATUS_CONFIG[s?.toUpperCase()] ?? DEFAULT_STATUS;
}

// ─── Failure type icon ───────────────────────────────────────────────────────

function FailureIcon({ type }: { type: string | null }) {
  switch (type?.toUpperCase()) {
    case "HIGH_CPU":      return <AlertTriangle className="h-3.5 w-3.5 text-[#ffaa00] shrink-0" />;
    case "CRITICAL_CPU":  return <AlertTriangle className="h-3.5 w-3.5 text-[#ff4444] shrink-0" />;
    case "INSTANCE_DOWN": return <Skull className="h-3.5 w-3.5 text-[#ff4444] shrink-0" />;
    case "STATUS_CHECK":  return <Search className="h-3.5 w-3.5 text-yellow-400 shrink-0" />;
    default:              return <CheckCircle2 className="h-3.5 w-3.5 text-[#00d4aa] shrink-0" />;
  }
}

function failureTextColor(type: string | null) {
  switch (type?.toUpperCase()) {
    case "HIGH_CPU":      return "text-[#ffaa00]";
    case "CRITICAL_CPU":
    case "INSTANCE_DOWN": return "text-[#ff4444]";
    default:              return "text-muted-foreground";
  }
}

// ─── Action badge ────────────────────────────────────────────────────────────

function ActionBadge({ action }: { action: string | null }) {
  switch (action?.toUpperCase()) {
    case "REBOOT_INSTANCE":
      return <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-mono font-semibold bg-[#ffaa00]/15 text-[#ffaa00]"><RefreshCw className="h-3 w-3" />REBOOT</span>;
    case "START_INSTANCE":
      return <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-mono font-semibold bg-[#00d4aa]/15 text-[#00d4aa]"><Play className="h-3 w-3" />START</span>;
    case "MONITORING":
      return <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-mono font-semibold bg-[#0088ff]/15 text-[#0088ff]"><Eye className="h-3 w-3" />MONITOR</span>;
    default:
      return <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-mono font-semibold bg-[#00d4aa]/15 text-[#00d4aa]"><CheckCircle2 className="h-3 w-3" />HEALTHY</span>;
  }
}

// ─── Event card ──────────────────────────────────────────────────────────────

const EventCard = ({ event }: { event: RecoveryEvent }) => {
  const cfg = getStatus(event.status);
  const instanceName = event.type !== "Monitor" ? event.type : "System";

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`rounded-lg border border-border border-l-4 ${cfg.border} bg-card overflow-hidden`}
    >
      {/* Header row */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider ${cfg.bg} ${cfg.text}`}>
            {cfg.label}
          </span>
          <span className="text-sm font-semibold text-foreground">{event.type}</span>
          <span className="text-[11px] font-mono text-muted-foreground truncate max-w-[140px]">{event.instance_id}</span>
        </div>
        <span className="text-[11px] font-mono text-muted-foreground shrink-0">{event.time}</span>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-3">

        {/* Failure reason */}
        <div className="flex items-start gap-2">
          <FailureIcon type={event.failure_type} />
          <div className="min-w-0">
            <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">
              Failure Reason
            </p>
            <p className={`text-[12px] font-mono ${failureTextColor(event.failure_type)}`}>
              {event.failure_reason ?? event.message ?? "No failure detected"}
            </p>
          </div>
        </div>

        {/* Action taken */}
        <div className="flex items-start gap-2">
          <Wrench className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">
              Action Taken
            </p>
            <ActionBadge action={event.action_taken} />
            {event.fix_applied && (
              <p className="text-[11px] font-mono text-muted-foreground mt-1">{event.fix_applied}</p>
            )}
          </div>
        </div>

        {/* Result */}
        {event.result && (
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-[#00d4aa] shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">
                Result
              </p>
              <p className="text-[12px] font-mono text-foreground">{event.result}</p>
            </div>
          </div>
        )}

        {/* Footer metrics */}
        {(event.cpu_at_failure !== null && event.cpu_at_failure !== undefined) && (
          <div className="flex items-center gap-4 pt-1 border-t border-border/40">
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground">
              <Activity className="h-3 w-3" />
              <span>CPU at failure: </span>
              <span className={`font-semibold ${event.cpu_at_failure >= 90 ? "text-[#ff4444]" : event.cpu_at_failure >= 70 ? "text-[#ffaa00]" : "text-[#00d4aa]"}`}>
                {event.cpu_at_failure.toFixed(1)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

// ─── SNS Setup Panel ─────────────────────────────────────────────────────────

interface SnsStatus {
  topic_exists: boolean;
  topic_arn: string | null;
  subscriptions: { protocol: string; endpoint: string; status: string }[];
  confirmed_count: number;
  message: string;
}

const SnsPanel = () => {
  const [status, setStatus] = useState<SnsStatus | null>(null);
  const [email, setEmail] = useState("");
  const [subscribing, setSubscribing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const loadStatus = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5000/api/sns/status");
      setStatus(await res.json());
    } catch {
      setStatus(null);
    }
  };

  useEffect(() => { if (open) loadStatus(); }, [open]);

  const subscribe = async () => {
    if (!email) return;
    setSubscribing(true);
    setMsg(null);
    try {
      const res = await fetch("http://127.0.0.1:5000/api/sns/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const json = await res.json();
      setMsg(json.message);
      loadStatus();
    } catch {
      setMsg("❌ Backend unreachable");
    } finally {
      setSubscribing(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-md border border-border bg-secondary/60 px-3 py-1.5 text-[11px] font-mono font-medium text-foreground hover:bg-secondary transition-colors"
      >
        📧 SNS Setup
      </button>
    );
  }

  return (
    <div className="w-full mt-3 rounded-lg border border-border bg-secondary/30 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-foreground">Email Alert Setup</span>
        <button onClick={() => setOpen(false)} className="text-[11px] font-mono text-muted-foreground hover:text-foreground">✕ Close</button>
      </div>

      {status && (
        <div className="space-y-1">
          <p className="text-[11px] font-mono" style={{ color: status.confirmed_count > 0 ? "#00d4aa" : "#ffaa00" }}>
            {status.message}
          </p>
          {status.subscriptions.map((s, i) => (
            <p key={i} className="text-[10px] font-mono text-muted-foreground">
              {s.endpoint} — {s.status === "PendingConfirmation" ? "⏳ Pending confirmation" : "✅ Confirmed"}
            </p>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-[11px] font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          onClick={subscribe}
          disabled={subscribing || !email}
          className="rounded-md border border-border bg-primary/20 px-3 py-1.5 text-[11px] font-mono font-medium text-primary hover:bg-primary/30 transition-colors disabled:opacity-50"
        >
          {subscribing ? "Sending..." : "Subscribe"}
        </button>
      </div>
      {msg && <p className="text-[11px] font-mono" style={{ color: msg.startsWith("❌") ? "#ff4444" : "#00d4aa" }}>{msg}</p>}
    </div>
  );
};

// ─── Main component ──────────────────────────────────────────────────────────

export const RecoveryEvents = () => {
  const [data, setData] = useState<RecoveryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [healing, setHealing] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [emailStatus, setEmailStatus] = useState<string | null>(null);

  const fetchEvents = useCallback(() => {
    fetch("http://127.0.0.1:5000/api/recovery")
      .then((res) => res.json())
      .then((raw) => {
        // Handle both old array format and new object format
        if (Array.isArray(raw)) {
          setData({ events: raw.slice(0, 10), total_recoveries: 0, last_recovery_time: null });
        } else {
          setData(raw);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 30_000);
    return () => clearInterval(interval);
  }, [fetchEvents]);

  const triggerHeal = async () => {
    setHealing(true);
    try {
      await fetch("http://127.0.0.1:5000/api/heal", { method: "POST" });
      await new Promise((r) => setTimeout(r, 800));
      fetchEvents();
    } finally {
      setHealing(false);
    }
  };

  const testEmail = async () => {
    setTestingEmail(true);
    setEmailStatus(null);
    try {
      const res = await fetch("http://127.0.0.1:5000/api/sns/test", { method: "POST" });
      const json = await res.json();
      setEmailStatus(json.status === "success" ? "✅ Test email sent — check inbox" : `❌ ${json.message}`);
    } catch {
      setEmailStatus("❌ Backend unreachable");
    } finally {
      setTestingEmail(false);
      setTimeout(() => setEmailStatus(null), 6000);
    }
  };

  const events = data?.events ?? [];
  const totalRecoveries = data?.total_recoveries ?? 0;
  const lastTime = data?.last_recovery_time;
  const activeCount = events.filter((e) =>
    ["TRIGGERED", "IN-PROGRESS", "RECOVERING"].includes(e.status?.toUpperCase())
  ).length;

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
        <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground">Recovery Events</h2>

        {totalRecoveries > 0 && (
          <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[11px] font-mono font-medium text-primary">
            {totalRecoveries} total recoveries
          </span>
        )}
        {activeCount > 0 && (
          <span className="rounded-full bg-[#ff4444]/15 px-2 py-0.5 text-[11px] font-mono font-medium text-[#ff4444]">
            {activeCount} active
          </span>
        )}
        {lastTime && (
          <span className="text-[11px] font-mono text-muted-foreground">
            Last: {lastTime}
          </span>
        )}

        <button
          onClick={triggerHeal}
          disabled={healing}
          className="ml-auto flex items-center gap-1.5 rounded-md border border-border bg-secondary/60 px-3 py-1.5 text-[11px] font-mono font-medium text-foreground hover:bg-secondary transition-colors disabled:opacity-50"
        >
          {healing ? (
            <><RefreshCw className="h-3 w-3 animate-spin" />Healing...</>
          ) : (
            <><Wrench className="h-3 w-3" />Trigger Heal</>
          )}
        </button>
        <button
          onClick={testEmail}
          disabled={testingEmail}
          className="flex items-center gap-1.5 rounded-md border border-border bg-secondary/60 px-3 py-1.5 text-[11px] font-mono font-medium text-foreground hover:bg-secondary transition-colors disabled:opacity-50"
        >
          {testingEmail ? (
            <><RefreshCw className="h-3 w-3 animate-spin" />Sending...</>
          ) : (
            <>📧 Test Email</>
          )}
        </button>
      </div>
      {emailStatus && (
        <p className="mb-3 text-[11px] font-mono px-1" style={{ color: emailStatus.startsWith("✅") ? "#00d4aa" : "#ff4444" }}>
          {emailStatus}
        </p>
      )}

      {/* SNS Setup Panel */}
      <SnsPanel />

      {/* Content */}
      {loading ? (
        <p className="text-xs text-muted-foreground px-3 py-2">Loading...</p>
      ) : events.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 gap-3">
          <CheckCircle2 className="h-10 w-10 text-[#00d4aa]" />
          <p className="text-sm font-mono font-medium text-[#00d4aa]">No failures detected — All systems healthy</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          <AnimatePresence initial={false}>
            {events.map((event, i) => (
              <EventCard key={`${event.instance_id}-${event.time}-${i}`} event={event} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};
