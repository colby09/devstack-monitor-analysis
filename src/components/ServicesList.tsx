import React, { useState, useEffect } from 'react'
import { Activity, CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react'

interface Service {
  id: string
  name: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  description: string
  port: number
  uptime: string
  lastCheck?: Date
  responseTime?: number
}

interface ServicesListProps {
  limit?: number
  searchTerm?: string
  showDetails?: boolean
}

const ServicesList: React.FC<ServicesListProps> = ({ 
  limit, 
  searchTerm = '',
  showDetails = false 
}) => {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchServices = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/services')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        
        // Transform the data to match the frontend interface
        const transformedServices: Service[] = data.map((service: any, index: number) => ({
          id: service.id || `service-${index}`,
          name: service.name,
          status: service.status,
          description: service.description,
          port: service.port || 0,
          uptime: service.uptime || '0h 0m',
          lastCheck: new Date(), // Default to now since we don't have this from backend
          responseTime: Math.floor(Math.random() * 100) + 20 // Mock response time for now
        }))
        
        setServices(transformedServices)
        setError(null)
      } catch (err) {
        console.error('Error fetching services:', err)
        setError('Failed to fetch services')
        // Fallback to empty array on error
        setServices([])
      } finally {
        setLoading(false)
      }
    }

    fetchServices()
  }, [])

  // Apply filtering and limiting to fetched services
  const filteredServices = React.useMemo(() => {
    let filtered = services

    if (searchTerm) {
      filtered = filtered.filter(service => 
        service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (service.description && service.description.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    if (limit) {
      filtered = filtered.slice(0, limit)
    }

    return filtered
  }, [services, searchTerm, limit])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'status-healthy'
      case 'warning':
        return 'status-warning'
      case 'critical':
        return 'status-critical'
      default:
        return 'status-unknown'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-success-600" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-warning-600" />
      case 'critical':
        return <XCircle className="h-5 w-5 text-danger-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-600" />
    }
  }

  const formatLastCheck = (date?: Date) => {
    if (!date) return 'N/A'
    
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
  }

  return (
    <div className="overflow-hidden">
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-b-2 border-primary-600 rounded-full mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">Loading services...</p>
        </div>
      )}
      
      {error && (
        <div className="text-center py-12">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
      
      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Service
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Port
                </th>
                {showDetails && (
                  <>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Uptime
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Check
                    </th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredServices.map((service) => (
              <tr key={service.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
                        <Activity className="h-5 w-5 text-primary-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{service.name}</div>
                      <div className="text-sm text-gray-500">{service.description}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(service.status)}
                    <span className={`ml-2 status-badge ${getStatusColor(service.status)}`}>
                      {service.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  :{service.port}
                </td>
                {showDetails && (
                  <>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {service.responseTime && service.responseTime > 0 ? `${service.responseTime}ms` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {service.uptime}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatLastCheck(service.lastCheck)}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
      
      {!loading && !error && filteredServices.length === 0 && (
        <div className="text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No services found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm 
              ? 'Try adjusting your search criteria.'
              : 'No services are currently configured.'
            }
          </p>
        </div>
      )}
    </div>
  )
}

export default ServicesList