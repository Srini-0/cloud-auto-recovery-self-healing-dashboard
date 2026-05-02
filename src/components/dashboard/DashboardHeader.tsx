import { useEffect, useState } from "react";
import { Cloud, RefreshCw, Circle } from "lucide-react";

interface DashboardHeaderProps {
  lastRefreshTime: number;
  onRefresh: () => void;
}

function formatElapsed(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ago`;
}

export const DashboardHeader = ({ lastRefreshTime, onRefresh }: DashboardHeaderProps) => {
  const [elapsed, setElapsed] = useState(() => formatElapsed(Date.now() - lastRefreshTime));

  useEffect(() => {
    setElapsed(formatElapsed(Date.now() - lastRefreshTime));
    // tick every second so the display stays accurate
    const id = setInterval(() => {
      setElapsed(formatElapsed(Date.now() - lastRefreshTime));
    }, 1_000);
    return () => clearInterval(id);
  }, [lastRefreshTime]);

  return (
    <header className="flex items-center justify-between py-4">
      <div className="flex items-center gap-3">
        <Cloud className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-lg font-bold tracking-tight text-foreground">Infrastructure Monitor</h1>
          <p className="text-xs font-mono text-muted-foreground">us-east-1 · prod environment</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
          <Circle className="h-2 w-2 fill-success text-success" />
          <span>Live</span>
        </div>
        <span className="text-xs font-mono text-muted-foreground">Last refresh: {elapsed}</span>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 rounded-md border border-border bg-secondary/60 px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>
    </header>
  );
};
