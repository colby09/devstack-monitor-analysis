import React, { useState, useEffect } from 'react'
import { Search, Filter, RefreshCw, Download, Trash2, HardDrive, Calendar, Database, AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react'

interface MemoryDump {
  id: string
  instance_id: string
  instance_name: string
  os_type: string
  dump_type: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  file_path: string
  file_size?: number
  created_at: string
  completed_at?: string
  error_message?: string
  ssh_host?: string
  checksum?: string
}

interface DumpStats {
  total_dumps: number
  completed_dumps: number
  failed_dumps: number
  in_progress_dumps: number
  total_size_gb: number
}

const DumpedRAM: React.FC = () => {
  const [dumps, setDumps] = useState<MemoryDump[]>([])
  const [stats, setStats] = useState<DumpStats | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDumps = async () => {
    try {
      setIsRefreshing(true)
      const [dumpsResponse, statsResponse] = await Promise.all([
        fetch('/api/dumps'),
        fetch('/api/dumps/stats')
      ])
      
      if (dumpsResponse.ok) {
        const dumpsData = await dumpsResponse.json()
        setDumps(dumpsData)
      }
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setStats(statsData)
      }
      
      setError(null)
    } catch (err) {
      console.error('Error fetching dumps:', err)
      setError('Failed to fetch memory dumps')
    } finally {
      setIsRefreshing(false)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDumps()
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchDumps, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleDownload = async (dump: MemoryDump) => {
    try {
      const response = await fetch(`/api/dumps/${dump.id}/download`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${dump.instance_name}_${dump.id}.dump`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Failed to download dump file')
      }
    } catch (error) {
      console.error('Error downloading dump:', error)
      alert('Error downloading dump file')
    }
  }

  const handleDelete = async (dump: MemoryDump) => {
    if (!confirm(`Are you sure you want to delete the memory dump for ${dump.instance_name}?`)) {
      return
    }
    
    try {
      const response = await fetch(`/api/dumps/${dump.id}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setDumps(prev => prev.filter(d => d.id !== dump.id))
        await fetchDumps() // Refresh stats
      } else {
        alert('Failed to delete dump')
      }
    } catch (error) {
      console.error('Error deleting dump:', error)
      alert('Error deleting dump')
    }
  }

  const filteredDumps = React.useMemo(() => {
    let filtered = dumps

    if (searchTerm) {
      filtered = filtered.filter(dump => 
        dump.instance_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dump.os_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dump.id.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(dump => dump.status === filterStatus)
    }

    return filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }, [dumps, searchTerm, filterStatus])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-600 animate-pulse" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-healthy'
      case 'in_progress':
        return 'status-warning'
      case 'failed':
        return 'status-critical'
      case 'pending':
        return 'status-unknown'
      default:
        return 'status-unknown'
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A'
    const gb = bytes / (1024 ** 3)
    if (gb >= 1) return `${gb.toFixed(2)} GB`
    const mb = bytes / (1024 ** 2)
    return `${mb.toFixed(2)} MB`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Memory Dumps</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage and download RAM dumps from OpenStack instances
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={fetchDumps}
            disabled={isRefreshing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Database className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Dumps</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.total_dumps}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircle className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Completed</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.completed_dumps}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">In Progress</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.in_progress_dumps}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <XCircle className="h-6 w-6 text-red-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Failed</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.failed_dumps}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <HardDrive className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Size</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.total_size_gb.toFixed(2)} GB</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1 max-w-lg">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search dumps..."
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
                <option value="completed">Completed</option>
                <option value="in_progress">In Progress</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Dumps Table */}
      <div className="card">
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-b-2 border-primary-600 rounded-full mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading memory dumps...</p>
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
                    OS Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Directory
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredDumps.map((dump) => (
                  <tr key={dump.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-lg bg-purple-100 flex items-center justify-center">
                            <HardDrive className="h-5 w-5 text-purple-600" />
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{dump.instance_name}</div>
                          <div className="text-sm text-gray-500">ID: {dump.instance_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(dump.status)}
                        <span className={`ml-2 status-badge ${getStatusColor(dump.status)}`}>
                          {dump.status.replace('_', ' ')}
                        </span>
                      </div>
                      {dump.error_message && (
                        <div className="text-xs text-red-600 mt-1">{dump.error_message}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dump.os_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatFileSize(dump.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(dump.created_at)}
                      {dump.completed_at && (
                        <div className="text-xs text-gray-500">
                          Completed: {formatDate(dump.completed_at)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {dump.file_path ? dump.file_path.substring(0, dump.file_path.lastIndexOf('/')) : '/tmp/ramdump'}
                      </div>
                      <div className="text-xs text-gray-500 break-all">
                        {dump.file_path.split('/').pop()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        {dump.status === 'completed' && (
                          <button
                            onClick={() => handleDownload(dump)}
                            className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(dump)}
                          className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredDumps.length === 0 && dumps.length > 0 && (
              <div className="text-center py-12">
                <HardDrive className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No dumps found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Try adjusting your search or filter criteria.
                </p>
              </div>
            )}
            
            {dumps.length === 0 && !loading && !error && (
              <div className="text-center py-12">
                <HardDrive className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No memory dumps found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Start by creating a memory dump from the Instances page.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default DumpedRAM
