import * as React from "react"
import { cn } from "../../utils/cn"

interface TabsProps {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}

const Tabs: React.FC<TabsProps> = ({ 
  defaultValue, 
  value, 
  onValueChange, 
  children, 
  className 
}) => {
  const [activeTab, setActiveTab] = React.useState(value || defaultValue || "")
  
  const handleTabChange = (newValue: string) => {
    setActiveTab(newValue)
    onValueChange?.(newValue)
  }

  return (
    <div className={cn("", className)}>
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement, { 
              activeTab, 
              onTabChange: handleTabChange 
            })
          : child
      )}
    </div>
  )
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
  activeTab?: string
  onTabChange?: (value: string) => void
}

const TabsList: React.FC<TabsListProps> = ({ 
  children, 
  className, 
  activeTab, 
  onTabChange 
}) => (
  <div
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500",
      className
    )}
  >
    {React.Children.map(children, (child) =>
      React.isValidElement(child)
        ? React.cloneElement(child as React.ReactElement, { 
            activeTab, 
            onTabChange 
          })
        : child
    )}
  </div>
)

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
  activeTab?: string
  onTabChange?: (value: string) => void
}

const TabsTrigger: React.FC<TabsTriggerProps> = ({ 
  value, 
  children, 
  className, 
  activeTab, 
  onTabChange 
}) => {
  const isActive = activeTab === value

  return (
    <button
      onClick={() => onTabChange?.(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-white text-gray-900 shadow-sm"
          : "text-gray-500 hover:text-gray-700",
        className
      )}
    >
      {children}
    </button>
  )
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
  activeTab?: string
}

const TabsContent: React.FC<TabsContentProps> = ({ 
  value, 
  children, 
  className, 
  activeTab 
}) => {
  if (activeTab !== value) return null

  return (
    <div
      className={cn(
        "mt-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
        className
      )}
    >
      {children}
    </div>
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
