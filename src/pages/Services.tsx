import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'
import ServicesList from '../components/ServicesList'

interface Service {
  name: string
  status: string
  port: number
  description?: string
  responseTime?: number
  uptime?: string
  lastCheck?: string
}

const Services: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)

  const fetchServices = async () => {
    try {
      const response = await fetch('/api/services')
      if (response.ok) {
        const data = await response.json()
        setServices(data)
      }
    } catch (error) {
      console.error('Error fetching services:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServices()
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchServices()
    setIsRefreshing(false)
  }

  // Calculate stats from real data
  const serviceStats = React.useMemo(() => {
    const total = services.length
    const healthy = services.filter(s => s.status === 'healthy').length
    const warning = services.filter(s => s.status === 'warning').length  
    const critical = services.filter(s => s.status === 'critical').length
    
    return { total, healthy, warning, critical }
  }, [services])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Services</h2>
          <p className="mt-1 text-sm text-gray-600">
            Monitor OpenStack core services and components
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Service Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-success-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Healthy</p>
              <p className="text-2xl font-semibold text-gray-900">{serviceStats.healthy}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertCircle className="h-8 w-8 text-warning-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Warning</p>
              <p className="text-2xl font-semibold text-gray-900">{serviceStats.warning}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertCircle className="h-8 w-8 text-danger-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Critical</p>
              <p className="text-2xl font-semibold text-gray-900">{serviceStats.critical}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-600 font-semibold">{serviceStats.total}</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total</p>
              <p className="text-2xl font-semibold text-gray-900">{serviceStats.total}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="max-w-lg">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search services..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Services List */}
      <div className="card">
        <ServicesList searchTerm={searchTerm} showDetails={true} />
      </div>
    </div>
  )
}

export default Services