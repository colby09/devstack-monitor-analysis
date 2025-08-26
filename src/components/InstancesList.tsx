import React, { useState, useEffect } from 'react'
import { Server, Play, Square, RotateCcw, Trash2, MoreHorizontal, Download, AlertCircle } from 'lucide-react'

interface Instance {
  id: string
  name: string
  status: 'active' | 'stopped' | 'error' | 'building'
  flavor: string
  image: string
  ip: string
  uptime: string
  cpu: number
  memory: number
}

interface InstancesListProps {
  limit?: number
  searchTerm?: string
  filterStatus?: string
  showActions?: boolean
}

const InstancesList: React.FC<InstancesListProps> = ({ 
  limit, 
  searchTerm = '', 
  filterStatus = 'all',
  showActions = false 
}) => {
  const [instances, setInstances] = useState<Instance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dumpingInstances, setDumpingInstances] = useState<Set<string>>(new Set())

  // Function to handle memory dump
  const handleDumpMemory = async (instance: Instance) => {
    if (dumpingInstances.has(instance.id)) return
    
    setDumpingInstances(prev => new Set([...prev, instance.id]))
    
    try {
      const response = await fetch(`/api/instances/${instance.id}/dump`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instance_id: instance.id,
          dump_type: 'physical_ram',
          ssh_user: 'root'
        })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to start memory dump: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      // Show success message
      alert(`Memory dump initiated for ${instance.name}. Dump ID: ${result.dump_id}`)
      
    } catch (error) {
      console.error('Error starting memory dump:', error)
      alert(`Failed to start memory dump for ${instance.name}: ${error}`)
    } finally {
      setDumpingInstances(prev => {
        const newSet = new Set(prev)
        newSet.delete(instance.id)
        return newSet
      })
    }
  }

  useEffect(() => {
    const fetchInstances = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/instances')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        
        // Transform the data to match the frontend interface
        const transformedInstances: Instance[] = data.map((instance: any) => ({
          id: instance.id,
          name: instance.name,
          status: instance.status,
          flavor: instance.flavor,
          image: instance.image,
          ip: instance.ip_address || 'N/A',
          uptime: instance.uptime || '0h 0m',
          cpu: instance.cpu_usage || 0,
          memory: instance.memory_usage || 0
        }))
        
        setInstances(transformedInstances)
        setError(null)
      } catch (err) {
        console.error('Error fetching instances:', err)
        setError('Failed to fetch instances')
        // Fallback to empty array on error
        setInstances([])
      } finally {
        setLoading(false)
      }
    }

    fetchInstances()
  }, [])

  // Apply filtering and limiting to fetched instances
  const filteredInstances = React.useMemo(() => {
    let filtered = instances

    if (searchTerm) {
      filtered = filtered.filter(instance => 
        instance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        instance.image.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(instance => instance.status === filterStatus)
    }

    if (limit) {
      filtered = filtered.slice(0, limit)
    }

    return filtered
  }, [instances, searchTerm, filterStatus, limit])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-healthy'
      case 'stopped':
        return 'status-unknown'
      case 'error':
        return 'status-critical'
      case 'building':
        return 'status-warning'
      default:
        return 'status-unknown'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Play className="h-4 w-4 text-success-600" />
      case 'stopped':
        return <Square className="h-4 w-4 text-gray-600" />
      case 'error':
        return <Trash2 className="h-4 w-4 text-danger-600" />
      case 'building':
        return <RotateCcw className="h-4 w-4 text-warning-600 animate-spin" />
      default:
        return <Server className="h-4 w-4 text-gray-600" />
    }
  }

  // Function to round numbers according to user specifications
  const roundValue = (value: number): number => {
    return Math.round(value)
  }

  return (
    <div className="overflow-hidden">
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-b-2 border-primary-600 rounded-full mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">Loading instances...</p>
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
                  Instance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flavor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resources
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uptime
                </th>
                {showActions && (
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInstances.map((instance) => (
              <tr key={instance.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
                        <Server className="h-5 w-5 text-primary-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{instance.name}</div>
                      <div className="text-sm text-gray-500">{instance.image}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(instance.status)}
                    <span className={`ml-2 status-badge ${getStatusColor(instance.status)}`}>
                      {instance.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {instance.flavor}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {instance.ip}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    CPU: {roundValue(instance.cpu)}% | RAM: {roundValue(instance.memory)}%
                  </div>
                  <div className="flex space-x-2 mt-1">
                    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                      <div 
                        className={`h-1.5 rounded-full ${instance.cpu > 80 ? 'bg-danger-500' : instance.cpu > 60 ? 'bg-warning-500' : 'bg-success-500'}`}
                        style={{ width: `${instance.cpu}%` }}
                      ></div>
                    </div>
                    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                      <div 
                        className={`h-1.5 rounded-full ${instance.memory > 80 ? 'bg-danger-500' : instance.memory > 60 ? 'bg-warning-500' : 'bg-success-500'}`}
                        style={{ width: `${instance.memory}%` }}
                      ></div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {instance.uptime}
                </td>
                {showActions && (
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handleDumpMemory(instance)}
                        disabled={dumpingInstances.has(instance.id) || instance.status !== 'active'}
                        className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md ${
                          instance.status === 'active' 
                            ? 'text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed'
                            : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                        }`}
                        title={instance.status === 'active' ? 'Dump RAM' : 'Instance must be active to dump RAM'}
                      >
                        {dumpingInstances.has(instance.id) ? (
                          <>
                            <RotateCcw className="h-3 w-3 mr-1 animate-spin" />
                            Dumping...
                          </>
                        ) : (
                          <>
                            <Download className="h-3 w-3 mr-1" />
                            Dump RAM
                          </>
                        )}
                      </button>
                      <button className="text-gray-400 hover:text-gray-600">
                        <MoreHorizontal className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredInstances.length === 0 && instances.length > 0 && (
          <div className="text-center py-12">
            <Server className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No instances found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search or filter criteria.
            </p>
          </div>
        )}
        
        {instances.length === 0 && !loading && !error && (
          <div className="text-center py-12">
            <Server className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No instances found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No instances are currently running.
            </p>
          </div>
        )}
      </div>
      )}
    </div>
  )
}

export default InstancesList