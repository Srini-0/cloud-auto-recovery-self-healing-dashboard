import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity } from "lucide-react";

type Mode = "1h" | "24h";

type InstanceSummary = {
  name: string;
};

type MetricsResponse = {
  labels: string[];
  timestamps: string[];
  instances: Record<string, Array<number | null>>;
};

type CPUPoint = {
  time: string;
  timestamp: string;
  [key: string]: string | number | null;
};

type Props = {
  instances: InstanceSummary[];
};

const COLORS = [
  "#ff7a1a", "#3b82f6", "#10b981", "#f43f5e", "#a855f7",
  "#eab308", "#06b6d4", "#ec4899", "#84cc16", "#f97316",
  "#6366f1", "#14b8a6", "#ef4444", "#8b5cf6", "#0ea5e9",
];

function buildColorMap(names: string[]): Record<string, string> {
  const map: Record<string, string> = {};
  [...names].sort().forEach((name, i) => {
    map[name] = COLORS[i % COLORS.length];
  });
  return map;
}

function emptyPoints(names: string[]): CPUPoint[] {
  return Array.from({ length: 13 }, (_, index) => {
    const point: CPUPoint = {
      time: `${index * 5}m`,
      timestamp: "",
    };
    names.forEach((name) => {
      point[name] = null;
    });
    return point;
  });
}

const formatTooltipTimestamp = (value: string) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).replace(",", "") + " UTC";
};

const formatAxisTimestamp = (value: string) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  });
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="min-w-[260px] rounded-xl border border-border bg-card/95 px-4 py-3 shadow-2xl backdrop-blur">
      <p className="mb-3 text-sm font-semibold text-foreground">{formatTooltipTimestamp(label)}</p>
      <div className="space-y-2">
        {payload.map((entry: any) => (
          <div key={entry.name} className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="h-1.5 w-4 rounded-full" style={{ backgroundColor: entry.color }} />
              <span>{entry.name}</span>
            </div>
            <span className="font-mono font-semibold text-foreground">
              {typeof entry.value === "number" ? entry.value.toFixed(2) : entry.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Injects SVG gradient defs into the recharts SVG via a custom component
const GradientDefs = ({ names, colorFor }: { names: string[]; colorFor: (n: string) => string }) => (
  <defs>
    {names.map((name) => (
      <linearGradient key={name} id={`grad-${name}`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={colorFor(name)} stopOpacity={0.4} />
        <stop offset="70%" stopColor={colorFor(name)} stopOpacity={0.08} />
        <stop offset="100%" stopColor={colorFor(name)} stopOpacity={0} />
      </linearGradient>
    ))}
  </defs>
);

export const CPUUtilizationChart = ({ instances }: Props) => {
  const propNames = [...instances.map((instance) => instance.name)].sort();
  const [mode, setMode] = useState<Mode>("1h");
  const [data, setData] = useState<CPUPoint[]>(() => emptyPoints(propNames));
  const [instanceNames, setInstanceNames] = useState<string[]>(propNames);
  const [colorMap, setColorMap] = useState<Record<string, string>>(() => buildColorMap(propNames));
  const [hoverTimestamp, setHoverTimestamp] = useState<string | null>(null);

  const colorFor = (name: string) => colorMap[name] ?? "#8b8b8b";

  useEffect(() => {
    let cancelled = false;

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/cpu-metrics?mode=${mode}`);
        const raw = (await response.json()) as MetricsResponse;

        if (cancelled || !raw.timestamps?.length || !raw.instances) return;

        const names = Object.keys(raw.instances).sort();
        let points = raw.timestamps.map((timestamp, index) => {
          const point: CPUPoint = {
            time: raw.labels[index] ?? formatAxisTimestamp(timestamp),
            timestamp,
          };
          names.forEach((name) => {
            point[name] = raw.instances[name]?.[index] ?? null;
          });
          return point;
        });

        // Trim leading/trailing all-null slots so the chart fills the visible area
        const hasData = (p: CPUPoint) => names.some((n) => p[n] !== null && p[n] !== undefined);
        const firstIdx = points.findIndex(hasData);
        const lastIdx = points.length - 1 - [...points].reverse().findIndex(hasData);
        if (firstIdx !== -1) {
          const bufferStart = Math.max(0, firstIdx - 3);
          points = points.slice(bufferStart, lastIdx + 1);
        }

        setInstanceNames(names);
        setColorMap(buildColorMap(names));
        setData(points);
      } catch {
        if (!cancelled && propNames.length > 0) {
          setInstanceNames(propNames);
          setColorMap(buildColorMap(propNames));
          setData(emptyPoints(propNames));
        }
      }
    };

    void fetchMetrics();

    const intervalId = window.setInterval(
      fetchMetrics,
      mode === "1h" ? 60_000 : 300_000
    );

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [mode]);

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-5 flex items-center gap-2">
        <Activity className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground">CPU Utilization (%)</h2>
        <div className="ml-auto flex items-center overflow-hidden rounded-md border border-border">
          {(["1h", "24h"] as Mode[]).map((value) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`px-3 py-1.5 text-[11px] font-mono font-medium transition-colors ${
                mode === value
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary/60 text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              {value.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {instanceNames.length === 0 ? (
        <div className="flex h-[320px] items-center justify-center">
          <p className="text-xs font-mono text-muted-foreground">No instances running</p>
        </div>
      ) : (
        <>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data}
                margin={{ top: 12, right: 16, bottom: 0, left: 8 }}
                onMouseMove={(state) => {
                  const activeLabel = state?.activeLabel;
                  setHoverTimestamp(typeof activeLabel === "string" ? activeLabel : null);
                }}
                onMouseLeave={() => setHoverTimestamp(null)}
              >
                <GradientDefs names={instanceNames} colorFor={colorFor} />
                <CartesianGrid stroke="hsl(220 14% 16%)" strokeDasharray="0" vertical horizontal />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatAxisTimestamp}
                  tick={{ fontSize: 11, fill: "hsl(215 12% 50%)", fontFamily: "JetBrains Mono, monospace" }}
                  tickLine={false}
                  axisLine={{ stroke: "hsl(220 14% 16%)" }}
                  minTickGap={24}
                />
                <YAxis
                  domain={([dataMin, dataMax]: [number, number]) => {
                    const allNull = dataMax === 0 && dataMin === 0;
                    if (allNull) return [0, 100];
                    const top = Math.max(dataMax * 1.3, 5);
                    return [0, Math.min(Math.ceil(top / 5) * 5, 100)];
                  }}
                  tickCount={5}
                  tickFormatter={(value) => `${value}%`}
                  tick={{ fontSize: 11, fill: "hsl(215 12% 50%)", fontFamily: "JetBrains Mono, monospace" }}
                  tickLine={false}
                  axisLine={false}
                />
                {hoverTimestamp && <ReferenceLine x={hoverTimestamp} stroke="#8b8b8b" strokeWidth={1} />}
                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{ stroke: "#8b8b8b", strokeWidth: 1 }}
                  labelFormatter={(label) => label}
                />
                {instanceNames.map((name) => (
                  <Area
                    key={name}
                    type="monotone"
                    dataKey={name}
                    connectNulls={true}
                    stroke={colorFor(name)}
                    strokeWidth={2.5}
                    fill={`url(#grad-${name})`}
                    dot={{ r: 3, strokeWidth: 0, fill: colorFor(name) }}
                    activeDot={{ r: 6, strokeWidth: 3, stroke: `${colorFor(name)}33`, fill: colorFor(name) }}
                    isAnimationActive={false}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Instance legend below chart */}
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 border-t border-border pt-4">
            {instanceNames.map((name) => (
              <span key={name} className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                <span
                  className="inline-block h-[3px] w-5 rounded-full"
                  style={{ backgroundColor: colorFor(name) }}
                />
                {name}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
