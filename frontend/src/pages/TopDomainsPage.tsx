import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Globe, TrendingUp, Activity } from 'lucide-react'
import { fetchDomainStats } from '@/services/api'
import toast from 'react-hot-toast'

interface DomainStat {
  domain: string
  count: number
}

export default function TopDomainsPage() {
  const [domainStats, setDomainStats] = useState<DomainStat[]>([])
  const [loading, setLoading] = useState(true)
  const [limit, setLimit] = useState(100)

  useEffect(() => {
    loadDomainStats()
  }, [limit])

  const loadDomainStats = async () => {
    try {
      setLoading(true)
      const data = await fetchDomainStats(limit)
      setDomainStats(data)
    } catch (error) {
      console.error('Failed to load domain stats:', error)
      toast.error('Failed to load domain statistics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Activity className="h-12 w-12 text-primary-500" />
        </motion.div>
      </div>
    )
  }

  const maxCount = domainStats.length > 0 ? Math.max(...domainStats.map(d => d.count)) : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Globe className="h-10 w-10 text-primary-500" />
          Top Domains
        </h1>
        <p className="text-dark-400">
          Most common domains across all credentials
        </p>
      </motion.div>

      {/* Limit Selector */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-dark-300">Show:</label>
        <div className="flex gap-2">
          {[20, 50, 100, 200].map((value) => (
            <button
              key={value}
              onClick={() => setLimit(value)}
              className={`px-4 py-2 rounded-lg transition-all ${
                limit === value
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-800/50 text-dark-300 hover:bg-dark-700/50'
              }`}
            >
              Top {value}
            </button>
          ))}
        </div>
      </div>

      {/* Domains List */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="card bg-dark-800/30 border border-dark-700/50 rounded-xl p-6"
      >
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary-400" />
          TOP {limit} DOMAINS
        </h2>

        {domainStats.length === 0 ? (
          <div className="text-center py-12 text-dark-400">
            <Globe className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p>No domain data available</p>
          </div>
        ) : (
          <div className="space-y-2">
            {domainStats.map((stat, index) => (
              <motion.div
                key={stat.domain}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.02 }}
                className="group hover:bg-dark-700/30 p-3 rounded-lg transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="text-dark-500 font-mono text-sm flex-shrink-0 w-8">
                      {index + 1}.
                    </span>
                    <Globe className="h-4 w-4 text-primary-400 flex-shrink-0" />
                    <span className="text-white font-medium truncate">
                      {stat.domain}
                    </span>
                  </div>
                  <span className="text-primary-400 font-bold ml-4 flex-shrink-0">
                    {stat.count.toLocaleString()}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-dark-700/50 rounded-full h-1.5 overflow-hidden ml-11">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(stat.count / maxCount) * 100}%` }}
                    transition={{ delay: index * 0.02 + 0.2, duration: 0.5 }}
                    className="bg-gradient-to-r from-primary-500 to-cyan-500 h-full"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-6 text-center text-dark-400"
      >
        Showing top {domainStats.length} domains
      </motion.div>
    </div>
  )
}
