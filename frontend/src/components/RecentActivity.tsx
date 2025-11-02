import { motion } from 'framer-motion'
import { useQuery } from 'react-query'
import { Clock, Shield, User, Globe } from 'lucide-react'
import { searchCredentials } from '@/services/api'

const activityVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: i * 0.1,
      type: "spring",
      stiffness: 100
    }
  })
}

export default function RecentActivity() {
  const { data: recentData, isLoading } = useQuery(
    'recent-credentials',
    () => searchCredentials({ limit: 10 }),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  )

  const recentCredentials = recentData?.results || []

  const getActivityIcon = (stealer?: string) => {
    if (stealer?.toLowerCase().includes('redline')) return Shield
    if (stealer?.toLowerCase().includes('raccoon')) return User
    return Globe
  }

  const getActivityColor = (stealer?: string) => {
    if (stealer?.toLowerCase().includes('redline')) return 'text-red-400'
    if (stealer?.toLowerCase().includes('raccoon')) return 'text-yellow-400'
    return 'text-blue-400'
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    return `${Math.floor(diffInSeconds / 86400)}d ago`
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center space-x-4 p-4 bg-dark-800/30 rounded-lg animate-pulse">
            <div className="w-10 h-10 bg-dark-700 rounded-lg"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-dark-700 rounded w-3/4"></div>
              <div className="h-3 bg-dark-700 rounded w-1/2"></div>
            </div>
            <div className="h-3 bg-dark-700 rounded w-16"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!recentCredentials || recentCredentials.length === 0) {
    return (
      <div className="text-center py-8 text-dark-400">
        <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No recent activity</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {recentCredentials.slice(0, 8).map((credential, index) => {
        const ActivityIcon = getActivityIcon(credential.stealer_name)
        const iconColor = getActivityColor(credential.stealer_name)
        
        return (
          <motion.div
            key={credential.id}
            custom={index}
            variants={activityVariants}
            initial="hidden"
            animate="visible"
            whileHover={{ scale: 1.02, x: 4 }}
            className="flex items-center space-x-4 p-4 bg-dark-800/30 rounded-lg border border-dark-700/50 hover:border-dark-600/50 transition-all duration-200 cursor-pointer group"
          >
            <div className={`p-2 rounded-lg bg-dark-700/50 group-hover:bg-dark-600/50 transition-colors`}>
              <ActivityIcon className={`h-5 w-5 ${iconColor}`} />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <p className="text-sm font-medium text-white truncate">
                  {credential.domain || credential.url || 'Unknown domain'}
                </p>
                {credential.stealer_name && (
                  <span className="px-2 py-1 text-xs bg-primary-500/20 text-primary-400 rounded-full">
                    {credential.stealer_name}
                  </span>
                )}
              </div>
              
              <p className="text-xs text-dark-400 truncate">
                {credential.username || 'No username'} • {credential.browser || 'Unknown browser'}
              </p>
            </div>
            
            <div className="text-xs text-dark-500 flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              {formatTimeAgo(credential.created_at)}
            </div>
          </motion.div>
        )
      })}
      
      {recentCredentials.length > 8 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center pt-4"
        >
          <button className="text-sm text-primary-400 hover:text-primary-300 transition-colors">
            View {recentCredentials.length - 8} more activities
          </button>
        </motion.div>
      )}
    </div>
  )
}
