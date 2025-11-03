import React, { useEffect, useState } from 'react'
import { fetchCreditCardStats, fetchCardBrandStats, CreditCardStats as StatsType, CardBrandStat } from '../services/api'

const CreditCardStats: React.FC = () => {
  const [stats, setStats] = useState<StatsType | null>(null)
  const [brandStats, setBrandStats] = useState<CardBrandStat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true)
        const [statsData, brandsData] = await Promise.all([
          fetchCreditCardStats(),
          fetchCardBrandStats()
        ])
        setStats(statsData)
        setBrandStats(brandsData)
      } catch (err) {
        setError('Failed to load credit card statistics')
        console.error('Error loading CC stats:', err)
      } finally {
        setIsLoading(false)
      }
    }

    loadStats()
  }, [])

  const getBrandColor = (brand: string) => {
    const colors: { [key: string]: string } = {
      'Visa': 'bg-blue-500',
      'Mastercard': 'bg-orange-500',
      'American Express': 'bg-green-500',
      'Discover': 'bg-purple-500',
      'JCB': 'bg-red-500',
      'Diners Club': 'bg-indigo-500',
      'Unknown': 'bg-gray-500'
    }
    return colors[brand] || 'bg-gray-500'
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse bg-white rounded-lg shadow p-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    )
  }

  if (!stats) return null

  const totalCards = stats.total_cards || 0
  const maxCount = brandStats.length > 0 ? Math.max(...brandStats.map(b => b.count)) : 1

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Credit Cards</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{totalCards.toLocaleString()}</p>
            </div>
            <div className="text-4xl">💳</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Unique Devices</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.unique_devices?.toLocaleString() || 0}</p>
            </div>
            <div className="text-4xl">🖥️</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Card Brands</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{brandStats.length}</p>
            </div>
            <div className="text-4xl">🏦</div>
          </div>
        </div>
      </div>

      {/* Brand Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Card Brand Distribution</h3>
        
        {brandStats.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No credit card data available</p>
        ) : (
          <div className="space-y-4">
            {brandStats.map((brandStat) => {
              const percentage = totalCards > 0 ? (brandStat.count / totalCards * 100) : 0
              const barWidth = maxCount > 0 ? (brandStat.count / maxCount * 100) : 0

              return (
                <div key={brandStat.brand}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{brandStat.brand}</span>
                    <span className="text-sm text-gray-600">
                      {brandStat.count.toLocaleString()} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`${getBrandColor(brandStat.brand)} h-3 rounded-full transition-all duration-500`}
                      style={{ width: `${barWidth}%` }}
                    ></div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Brand Pie Chart (Simple Text-based) */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Card Brands</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {brandStats.slice(0, 6).map((brandStat) => (
            <div 
              key={brandStat.brand}
              className="border border-gray-200 rounded-lg p-4 text-center hover:shadow-md transition-shadow"
            >
              <div className={`w-16 h-16 mx-auto mb-3 rounded-full ${getBrandColor(brandStat.brand)} flex items-center justify-center text-white text-2xl font-bold`}>
                {brandStat.brand.charAt(0)}
              </div>
              <p className="text-sm font-semibold text-gray-900">{brandStat.brand}</p>
              <p className="text-2xl font-bold text-gray-700 mt-1">{brandStat.count}</p>
              <p className="text-xs text-gray-500">
                {totalCards > 0 ? ((brandStat.count / totalCards * 100).toFixed(1)) : 0}%
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CreditCardStats
