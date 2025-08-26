import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, MemoryStick, Server, Zap } from 'lucide-react';

interface MetricData {
  cpu: {
    current: number;
    unit: string;
  };
  memory: {
    current: number;
    unit: string;
  };
  disk: {
    current: number;
    unit: string;
  };
  instances: {
    running: number;
    total: number;
  };
  services: {
    active: number;
    total: number;
  };
}

const MetricsCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  description?: string;
  color?: string;
}> = ({ title, value, icon, description, color = 'text-blue-600' }) => (
  <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <div className={color}>{icon}</div>
    </div>
    <div className="text-2xl font-bold text-gray-900">{value}</div>
    {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
  </div>
);

export default function Metrics() {
  const [data, setData] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetricsSummary = async () => {
    try {
      setLoading(true);
      // Use relative URL to avoid CORS issues
      const response = await fetch('/api/metrics/summary');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      console.log('Metrics data received:', result);
      setData(result);
      setError(null);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsSummary();
    // Aggiorna ogni 30 secondi
    const interval = setInterval(fetchMetricsSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Metrics</h1>
        <div className="text-center">Loading metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Metrics</h1>
        <div className="text-center text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Metrics</h1>
        <div className="text-center">No data available</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">System Metrics</h1>
        <p className="text-sm text-gray-500">
          Real-time values • Updates every 30 seconds
        </p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <MetricsCard
          title="CPU Usage"
          value={`${data.cpu.current}${data.cpu.unit}`}
          icon={<Cpu className="h-4 w-4" />}
          description="Current processor usage"
          color={data.cpu.current > 80 ? 'text-red-600' : data.cpu.current > 60 ? 'text-yellow-600' : 'text-green-600'}
        />
        
        <MetricsCard
          title="Memory Usage"
          value={`${data.memory.current}${data.memory.unit}`}
          icon={<MemoryStick className="h-4 w-4" />}
          description="Current RAM usage"
          color={data.memory.current > 80 ? 'text-red-600' : data.memory.current > 60 ? 'text-yellow-600' : 'text-green-600'}
        />
        
        <MetricsCard
          title="Disk Usage"
          value={`${data.disk.current}${data.disk.unit}`}
          icon={<HardDrive className="h-4 w-4" />}
          description="Current disk space usage"
          color={data.disk.current > 90 ? 'text-red-600' : data.disk.current > 75 ? 'text-yellow-600' : 'text-green-600'}
        />
        
        <MetricsCard
          title="Running Instances"
          value={`${data.instances.running}/${data.instances.total}`}
          icon={<Server className="h-4 w-4" />}
          description="Active OpenStack instances"
          color={data.instances.running === data.instances.total ? 'text-green-600' : 'text-yellow-600'}
        />
        
        <MetricsCard
          title="Active Services"
          value={`${data.services.active}/${data.services.total}`}
          icon={<Zap className="h-4 w-4" />}
          description="Running OpenStack services"
          color={data.services.active === data.services.total ? 'text-green-600' : 'text-red-600'}
        />
        
        <MetricsCard
          title="System Status"
          value={data.cpu.current < 80 && data.memory.current < 80 ? 'Healthy' : 'Warning'}
          icon={<Activity className="h-4 w-4" />}
          description="Overall system health"
          color={data.cpu.current < 80 && data.memory.current < 80 ? 'text-green-600' : 'text-yellow-600'}
        />
      </div>
    </div>
  );
}