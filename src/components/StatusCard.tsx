import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '../utils/cn'

interface StatusCardProps {
  title: string
  value: string
  subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  trend?: 'up' | 'down'
  trendValue?: string
  color?: 'success' | 'warning' | 'danger' | 'primary'
}

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  color = 'primary'
}) => {
  const colorClasses = {
    success: 'text-success-600 bg-success-50',
    warning: 'text-warning-600 bg-warning-50',
    danger: 'text-danger-600 bg-danger-50',
    primary: 'text-primary-600 bg-primary-50'
  }

  const trendColorClasses = {
    up: 'text-success-600',
    down: 'text-danger-600'
  }

  return (
    <div className="card">
      <div className="flex items-center">
        <div className={cn('flex-shrink-0 p-3 rounded-lg', colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {subtitle && (
              <p className="ml-2 text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
          {trend && trendValue && (
            <div className={cn('flex items-center mt-1', trendColorClasses[trend])}>
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              <span className="text-sm font-medium">{trendValue}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatusCard