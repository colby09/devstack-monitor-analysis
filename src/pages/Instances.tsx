import React, { useState, useEffect } from 'react'
import { Search, Filter, RefreshCw, WifiOff } from 'lucide-react'
import InstancesList from '../components/InstancesList'

const Instances: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [hasInstances, setHasInstances] = useState(true)
  const [openStackConnected, setOpenStackConnected] = useState(true)

  useEffect(() => {
    // Check if OpenStack is connected by looking at instances
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/instances')
        const instances = await response.json()
        setHasInstances(instances.length > 0)
        
        // Also check services to see if we have connection
        const servicesResponse = await fetch('/api/services')
        const services = await servicesResponse.json()
        const hasConnectionError = services.some((s: any) => s.name === 'openstack-connection')
        setOpenStackConnected(!hasConnectionError)
      } catch (error) {
        setOpenStackConnected(false)
        setHasInstances(false)
      }
    }
    
    checkConnection()
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Instances</h2>
          <p className="mt-1 text-sm text-gray-600">
            Monitor and manage your OpenStack instances
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

      {/* No OpenStack Connection Message */}
      {!openStackConnected && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center">
            <WifiOff className="h-6 w-6 text-yellow-600 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-yellow-800">
                No OpenStack Connection
              </h3>
              <p className="text-sm text-yellow-600 mt-1">
                Connect to DevStack on localhost:5000 to view instances. No mock data is shown to avoid confusion.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters - Only show if connected */}
      {openStackConnected && (
        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1 max-w-lg">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search instances..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 rounded-md"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="stopped">Stopped</option>
                  <option value="error">Error</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instances List - Only show if connected */}
      {openStackConnected && (
        <div className="card">
          <InstancesList 
            searchTerm={searchTerm}
            filterStatus={filterStatus}
            showActions={true}
          />
        </div>
      )}
    </div>
  )
}

export default Instances
