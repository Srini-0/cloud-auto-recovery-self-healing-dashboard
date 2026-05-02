import { useEffect, useState } from "react";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { MetricCards } from "@/components/dashboard/MetricCards";
import { EC2StatusPanel } from "@/components/dashboard/EC2StatusPanel";
import { CPUUtilizationChart } from "@/components/dashboard/CPUUtilizationChart";
import { CloudWatchAlarms } from "@/components/dashboard/CloudWatchAlarms";
import { AutoScalingLogs } from "@/components/dashboard/AutoScalingLogs";
import { RecoveryEvents } from "@/components/dashboard/RecoveryEvents";

type SummaryResponse = {
  total_instances: number;
  healthy_instances: number;
  unhealthy_instances: number;
  avg_cpu: number;
};

type InstanceResponse = {
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

const API_BASE_URL = "http://127.0.0.1:5000";

const REFRESH_KEY = "dashboard_last_refresh";

const Index = () => {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [instances, setInstances] = useState<InstanceResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshTime, setLastRefreshTime] = useState<number>(() => {
    const stored = sessionStorage.getItem(REFRESH_KEY);
    return stored ? parseInt(stored, 10) : Date.now();
  });

  const updateRefreshTime = () => {
    const now = Date.now();
    sessionStorage.setItem(REFRESH_KEY, String(now));
    setLastRefreshTime(now);
  };

  const loadDashboardData = async () => {
    let cancelled = false;
    try {
      setIsLoading(true);
      const [summaryRes, instancesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/summary`),
        fetch(`${API_BASE_URL}/api/instances`),
      ]);

      if (!summaryRes.ok || !instancesRes.ok) {
        throw new Error("Unable to load dashboard data from backend.");
      }

      const [summaryData, instancesData] = await Promise.all([
        summaryRes.json() as Promise<SummaryResponse>,
        instancesRes.json() as Promise<InstanceResponse[]>,
      ]);

      if (!cancelled) {
        setSummary(summaryData);
        setInstances(instancesData);
        updateRefreshTime();
        setError(null);
      }
    } catch {
      if (!cancelled) {
        setSummary(null);
        setInstances([]);
        setError("Backend unavailable. Start Flask on http://127.0.0.1:5000.");
      }
    } finally {
      if (!cancelled) {
        setIsLoading(false);
      }
    }
    return () => { cancelled = true; };
  };

  useEffect(() => {
    void loadDashboardData();
    // Poll every 30s so new/terminated instances reflect automatically
    const interval = setInterval(() => void loadDashboardData(), 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    void loadDashboardData();
  };

  return (
    <div className="min-h-screen bg-background px-6 pb-10">
      <div className="mx-auto max-w-[1400px]">
        <DashboardHeader lastRefreshTime={lastRefreshTime} onRefresh={handleRefresh} />
        <div className="space-y-5">
          <MetricCards summary={summary} isLoading={isLoading} />
          <EC2StatusPanel instances={instances} isLoading={isLoading} error={error} />
          <CPUUtilizationChart instances={instances} />
          <div className="grid grid-cols-2 gap-5">
            <CloudWatchAlarms />
            <AutoScalingLogs />
          </div>
          <RecoveryEvents />
        </div>
      </div>
    </div>
  );
};

export default Index;
