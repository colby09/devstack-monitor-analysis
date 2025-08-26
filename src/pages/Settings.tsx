import React, { useState, useEffect } from 'react'
import { Save, Bell, Shield, Database, Wifi, CheckCircle, XCircle, RefreshCw } from 'lucide-react'

interface ConnectionInfo {
  status: string
  auth_url: string
  project_name: string
  user_domain: string
  project_domain: string
  username: string
  region: string
  identity_api_version: string
  compute_api_version: string
  image_api_version: string
  network_api_version: string
  last_tested: string
  error?: string
  compute_accessible?: boolean
  image_accessible?: boolean
  network_accessible?: boolean
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      slack: false
    },
    monitoring: {
      interval: 30,
      retries: 3,
      timeout: 10
    },
    alerts: {
      cpu_threshold: 80,
      memory_threshold: 85,
      disk_threshold: 90
    }
  })

  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo | null>(null)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)

  const testOpenStackConnection = async () => {
    setIsTestingConnection(true)
    setConnectionError(null)
    
    try {
      const response = await fetch('/api/system/connection/test')
      const data = await response.json()
      
      if (data.success) {
        setConnectionInfo(data.connection)
        setConnectionError(null)
      } else {
        setConnectionError(data.error || 'Connection test failed')
        setConnectionInfo(data.connection || null)
      }
    } catch (error) {
      console.error('Connection test error:', error)
      setConnectionError('Failed to test connection')
      setConnectionInfo(null)
    } finally {
      setIsTestingConnection(false)
    }
  }

  // Test connection on component mount
  useEffect(() => {
    testOpenStackConnection()
  }, [])

  const handleSave = () => {
    // Save settings logic
    console.log('Settings saved:', settings)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
          <p className="mt-1 text-sm text-gray-600">
            Configure monitoring preferences and system settings
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={handleSave}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </button>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Bell className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Email Notifications</label>
              <p className="text-sm text-gray-500">Receive alerts via email</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.email}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                notifications: { ...prev.notifications, email: e.target.checked }
              }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Push Notifications</label>
              <p className="text-sm text-gray-500">Browser push notifications</p>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.push}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                notifications: { ...prev.notifications, push: e.target.checked }
              }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* Monitoring Settings */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Wifi className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Monitoring</h3>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Check Interval (seconds)
            </label>
            <input
              type="number"
              value={settings.monitoring.interval}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                monitoring: { ...prev.monitoring, interval: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Retry Attempts
            </label>
            <input
              type="number"
              value={settings.monitoring.retries}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                monitoring: { ...prev.monitoring, retries: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timeout (seconds)
            </label>
            <input
              type="number"
              value={settings.monitoring.timeout}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                monitoring: { ...prev.monitoring, timeout: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Alert Thresholds */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Shield className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Alert Thresholds</h3>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CPU Usage (%)
            </label>
            <input
              type="number"
              value={settings.alerts.cpu_threshold}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                alerts: { ...prev.alerts, cpu_threshold: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Memory Usage (%)
            </label>
            <input
              type="number"
              value={settings.alerts.memory_threshold}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                alerts: { ...prev.alerts, memory_threshold: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Disk Usage (%)
            </label>
            <input
              type="number"
              value={settings.alerts.disk_threshold}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                alerts: { ...prev.alerts, disk_threshold: parseInt(e.target.value) }
              }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Connection Settings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Database className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">OpenStack Connection</h3>
          </div>
          <button
            onClick={testOpenStackConnection}
            disabled={isTestingConnection}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isTestingConnection ? 'animate-spin' : ''}`} />
            {isTestingConnection ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
        
        {/* Connection Status */}
        {connectionInfo && (
          <div className="mb-6 p-4 rounded-lg border">
            <div className="flex items-center mb-3">
              {connectionInfo.status === 'connected' ? (
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500 mr-2" />
              )}
              <span className={`font-medium ${
                connectionInfo.status === 'connected' ? 'text-green-700' : 'text-red-700'
              }`}>
                {connectionInfo.status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
              <span className="ml-2 text-sm text-gray-500">
                Last tested: {new Date(connectionInfo.last_tested).toLocaleString()}
              </span>
            </div>
            
            {connectionError && (
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{connectionError}</p>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Auth URL:</span>
                <span className="ml-2 text-gray-600">{connectionInfo.auth_url}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Project:</span>
                <span className="ml-2 text-gray-600">{connectionInfo.project_name}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Username:</span>
                <span className="ml-2 text-gray-600">{connectionInfo.username}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Region:</span>
                <span className="ml-2 text-gray-600">{connectionInfo.region}</span>
              </div>
            </div>
            
            {/* API Versions */}
            <div className="mt-4">
              <h4 className="font-medium text-gray-700 mb-2">API Versions & Accessibility</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    connectionInfo.identity_api_version && connectionInfo.identity_api_version !== 'Unknown' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span>Identity: {connectionInfo.identity_api_version}</span>
                </div>
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    connectionInfo.compute_api_version && connectionInfo.compute_api_version !== 'Unknown' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span>Compute: {connectionInfo.compute_api_version}</span>
                </div>
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    connectionInfo.image_api_version && connectionInfo.image_api_version !== 'Unknown' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span>Image: {connectionInfo.image_api_version}</span>
                </div>
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    connectionInfo.network_api_version && connectionInfo.network_api_version !== 'Unknown' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span>Network: {connectionInfo.network_api_version}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Connection Configuration (Display Only) */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Keystone URL
            </label>
            <input
              type="url"
              value={connectionInfo?.auth_url || 'http://localhost:5000/v3'}
              readOnly
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project Name
            </label>
            <input
              type="text"
              value={connectionInfo?.project_name || 'admin'}
              readOnly
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-600"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings