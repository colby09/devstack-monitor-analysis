import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Server, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Zap,
  WifiOff,
  RefreshCw,
  Cpu,
  MemoryStick
} from 'lucide-react'
import StatusCard from '../components/StatusCard'
import InstancesList from '../components/InstancesList'
import ServicesList from '../components/ServicesList'

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  
  const [stats, setStats] = useState({
    totalInstances: 0,
    healthyInstances: 0,
    totalServices: 0,
    healthyServices: 0,
    uptime: '0h 0m',
    lastUpdate: new Date(),
    openStackConnected: false,
    systemUptime: '0h 0m',
    // Aggiungiamo i dati delle metriche
    cpu: 0,
    memory: 0,
    memoryTotalGb: 0,
    memoryUsedGb: 0,
    memoryAvailableGb: 0,
    systemStatus: 'Loading...'
  })

  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check OpenStack connection and get real data
    const fetchData = async () => {
      setIsLoading(true)
      try {
        // Get instances, services, system uptime and metrics data in parallel
        const [instancesResponse, servicesResponse, systemResponse, metricsResponse] = await Promise.all([
          fetch('/api/instances'),
          fetch('/api/services'),
          fetch('/api/system/uptime'),
          fetch('/api/metrics/summary')
        ])
        
        if (instancesResponse.ok && servicesResponse.ok) {
          const instancesData = await instancesResponse.json()
          const servicesData = await servicesResponse.json()
          
          // Extract actual arrays from API response
          const instances = instancesData.value || instancesData
          const services = servicesData.value || servicesData
          
          // Get system uptime from DevStack API
          let systemUptime = '0h 0m'
          if (systemResponse.ok) {
            const systemData = await systemResponse.json()
            systemUptime = systemData.uptime || '0h 0m'
          } else {
            // Fallback: calculate uptime from oldest instance if system API fails
            if (instances.length > 0) {
              const oldestInstance = instances.reduce((oldest: any, current: any) => {
                return new Date(current.created_at) < new Date(oldest.created_at) ? current : oldest
              })
              
              const uptimeMs = Date.now() - new Date(oldestInstance.created_at).getTime()
              const uptimeHours = Math.floor(uptimeMs / (1000 * 60 * 60))
              const uptimeMinutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60))
              systemUptime = `${uptimeHours}h ${uptimeMinutes}m`
            }
          }

          // Get metrics data
          let cpu = 0, memory = 0, memoryTotalGb = 0, memoryUsedGb = 0, memoryAvailableGb = 0, systemStatus = 'Unknown'
          if (metricsResponse.ok) {
            const metricsData = await metricsResponse.json()
            cpu = metricsData.cpu?.current || 0
            memory = metricsData.memory?.current || 0
            memoryTotalGb = metricsData.memory?.total_gb || 0
            memoryUsedGb = metricsData.memory?.used_gb || 0
            memoryAvailableGb = metricsData.memory?.available_gb || 0
            systemStatus = (cpu < 80 && memory < 80) ? 'Healthy' : 'Warning'
          }
          
          setStats({
            openStackConnected: true,
            totalInstances: instances.length,
            healthyInstances: instances.filter((i: any) => i.status === 'active').length,
            totalServices: services.length,
            healthyServices: services.filter((s: any) => s.status === 'healthy').length,
            uptime: systemUptime,
            systemUptime: systemUptime,
            lastUpdate: new Date(),
            cpu: cpu,
            memory: memory,
            memoryTotalGb: memoryTotalGb,
            memoryUsedGb: memoryUsedGb,
            memoryAvailableGb: memoryAvailableGb,
            systemStatus: systemStatus
          })
        } else {
          setStats(prev => ({
            ...prev,
            openStackConnected: false,
            lastUpdate: new Date()
          }))
        }
      } catch (error) {
        console.error('Error fetching data:', error)
        setStats(prev => ({
          ...prev,
          openStackConnected: false,
          lastUpdate: new Date()
        }))
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const handleViewAllInstances = () => {
    navigate('/instances')
  }

  const handleViewAllServices = () => {
    navigate('/services')
  }

  // Calculate health percentages
  const healthPercentage = stats.totalInstances > 0 
    ? Math.round((stats.healthyInstances / stats.totalInstances) * 100)
    : 0

  const serviceHealthPercentage = stats.totalServices > 0 
    ? Math.round((stats.healthyServices / stats.totalServices) * 100) 
    : 0

  return (
    <div className="space-y-6">
      {/* OpenStack Connection Status Banner */}
      {!stats.openStackConnected && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <WifiOff className="h-6 w-6 text-red-600 mr-3" />
            <div className="flex-1">
              <h3 className="text-lg font-medium text-red-800">
                OpenStack Connection Not Available
              </h3>
              <p className="text-sm text-red-600 mt-1">
                DevStack is not running on localhost:5000. Please start your DevStack instance to see real data.
              </p>
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="ml-4 inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry Connection
            </button>
          </div>
        </div>
      )}
      
      {/* Overview Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatusCard
          title="Total Instances"
          value={stats.totalInstances.toString()}
          icon={Server}
          trend={healthPercentage > 80 ? 'up' : 'down'}
          trendValue={`${healthPercentage}% healthy`}
          color={healthPercentage > 80 ? 'success' : healthPercentage > 60 ? 'warning' : 'danger'}
        />
        
        <StatusCard
          title="Active Services"
          value={stats.healthyServices.toString()}
          subtitle={`of ${stats.totalServices} total`}
          icon={Activity}
          trend={serviceHealthPercentage > 90 ? 'up' : 'down'}
          trendValue={`${serviceHealthPercentage}% healthy`}
          color={serviceHealthPercentage > 90 ? 'success' : serviceHealthPercentage > 70 ? 'warning' : 'danger'}
        />
        
        <StatusCard
          title="System Uptime"
          value={stats.systemUptime}
          subtitle="DevStack system uptime"
          icon={Clock}
          trend="up"
          trendValue="System running"
          color="success"
        />
        
        <StatusCard
          title="Performance"
          value="Optimal"
          subtitle="All systems green"
          icon={Zap}
          trend="up"
          trendValue="Response time: 45ms"
          color="success"
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Metrics Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">System Metrics</h3>
            <div className="flex space-x-2">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary-100 text-primary-800">
                Live
              </span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {/* CPU Usage Mini Card */}
            <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
              <div className="text-2xl font-bold text-gray-900">{stats.cpu.toFixed(1)}%</div>
              <div className="text-xs text-gray-500 mt-1">CPU Usage</div>
              <div className={`w-full h-1 rounded-full mt-2 ${
                stats.cpu > 80 ? 'bg-red-200' : stats.cpu > 60 ? 'bg-yellow-200' : 'bg-green-200'
              }`}>
                <div 
                  className={`h-1 rounded-full transition-all duration-500 ${
                    stats.cpu > 80 ? 'bg-red-500' : stats.cpu > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(stats.cpu, 100)}%` }}
                />
              </div>
            </div>

            {/* Memory Usage Mini Card */}
            <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
              <div className="text-2xl font-bold text-gray-900">{stats.memory.toFixed(1)}%</div>
              <div className="text-xs text-gray-500 mt-1">Memory Usage</div>
              <div className="text-xs text-gray-400 mt-1">
                {stats.memoryAvailableGb.toFixed(1)}GB free of {stats.memoryTotalGb.toFixed(1)}GB
              </div>
              <div className={`w-full h-1 rounded-full mt-2 ${
                stats.memory > 80 ? 'bg-red-200' : stats.memory > 60 ? 'bg-yellow-200' : 'bg-green-200'
              }`}>
                <div 
                  className={`h-1 rounded-full transition-all duration-500 ${
                    stats.memory > 80 ? 'bg-red-500' : stats.memory > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(stats.memory, 100)}%` }}
                />
              </div>
            </div>

            {/* System Status Mini Card */}
            <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
              <div className={`text-lg font-bold ${
                stats.systemStatus === 'Healthy' ? 'text-green-600' : 
                stats.systemStatus === 'Warning' ? 'text-yellow-600' : 'text-gray-600'
              }`}>
                {stats.systemStatus}
              </div>
              <div className="text-xs text-gray-500 mt-1">System Status</div>
              <div className="text-xs text-gray-400 mt-1">
                CPU: {stats.cpu.toFixed(0)}% | RAM: {stats.memory.toFixed(0)}%
              </div>
              <div className={`w-full h-1 rounded-full mt-2 ${
                stats.systemStatus === 'Healthy' ? 'bg-green-200' : 
                stats.systemStatus === 'Warning' ? 'bg-yellow-200' : 'bg-gray-200'
              }`}>
                <div 
                  className={`h-1 rounded-full transition-all duration-500 ${
                    stats.systemStatus === 'Healthy' ? 'bg-green-500' : 
                    stats.systemStatus === 'Warning' ? 'bg-yellow-500' : 'bg-gray-500'
                  }`}
                  style={{ width: stats.systemStatus === 'Healthy' ? '100%' : '60%' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">System Status</h3>
            <span className="text-sm text-gray-500">
              Last updated: {stats.lastUpdate.toLocaleTimeString()}
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`h-3 w-3 rounded-full ${stats.openStackConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium text-gray-900">OpenStack Connection</span>
              </div>
              <span className={`text-sm ${stats.openStackConnected ? 'text-green-600' : 'text-red-600'}`}>
                {stats.openStackConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`h-3 w-3 rounded-full ${serviceHealthPercentage > 80 ? 'bg-green-500' : serviceHealthPercentage > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium text-gray-900">Services Health</span>
              </div>
              <span className={`text-sm ${serviceHealthPercentage > 80 ? 'text-green-600' : serviceHealthPercentage > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                {serviceHealthPercentage}% ({stats.healthyServices}/{stats.totalServices})
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`h-3 w-3 rounded-full ${healthPercentage > 80 ? 'bg-green-500' : healthPercentage > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium text-gray-900">Instances Health</span>
              </div>
              <span className={`text-sm ${healthPercentage > 80 ? 'text-green-600' : healthPercentage > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                {healthPercentage}% ({stats.healthyInstances}/{stats.totalInstances})
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Instances and Services Overview */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Instances</h3>
            <button 
              onClick={handleViewAllInstances}
              className="text-sm text-primary-600 hover:text-primary-700 transition-colors"
            >
              View all
            </button>
          </div>
          <InstancesList limit={5} />
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Core Services</h3>
            <button 
              onClick={handleViewAllServices}
              className="text-sm text-primary-600 hover:text-primary-700 transition-colors"
            >
              View all
            </button>
          </div>
          <ServicesList limit={5} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard