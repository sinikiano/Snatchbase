import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Filter, 
  X, 
  Download,
  Eye,
  EyeOff,
  Copy,
  Globe,
  User,
  Key,
  Chrome,
  Shield,
  ChevronDown
} from 'lucide-react'
import { searchCredentials, Credential } from '@/services/api'
import toast from 'react-hot-toast'
import CredentialCard from '@/components/CredentialCard'

export default function SearchNew() {
  const [searchQuery, setSearchQuery] = useState('')
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [showFilters, setShowFilters] = useState(false)
  const [showPasswords, setShowPasswords] = useState(false)
  
  // Filters
  const [filters, setFilters] = useState({
    domain: '',
    username: '',
    browser: '',
    tld: '',
    stealer_name: ''
  })

  useEffect(() => {
    if (searchQuery || Object.values(filters).some(v => v)) {
      handleSearch()
    }
  }, [page])

  const handleSearch = async () => {
    try {
      setLoading(true)
      const response = await searchCredentials({
        q: searchQuery || undefined,
        domain: filters.domain || undefined,
        username: filters.username || undefined,
        browser: filters.browser || undefined,
        tld: filters.tld || undefined,
        limit: 50,
        offset: page * 50
      })
      
      setCredentials(response.results)
      setTotal(response.total)
    } catch (error) {
      console.error('Search failed:', error)
      toast.error('Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      setPage(0)
      handleSearch()
    }
  }

  const clearFilters = () => {
    setFilters({
      domain: '',
      username: '',
      browser: '',
      tld: '',
      stealer_name: ''
    })
    setSearchQuery('')
    setCredentials([])
    setTotal(0)
  }

  const exportResults = () => {
    const csv = [
      ['Domain', 'URL', 'Username', 'Password', 'Browser', 'TLD', 'Stealer'].join(','),
      ...credentials.map(c => [
        c.domain || '',
        c.url || '',
        c.username || '',
        c.password || '',
        c.browser || '',
        c.tld || '',
        c.stealer_name || ''
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `credentials-${Date.now()}.csv`
    a.click()
    toast.success('Exported to CSV')
  }

  const exportTxt = async () => {
    try {
      // Build query params
      const params = new URLSearchParams()
      if (searchQuery) params.append('q', searchQuery)
      if (filters.domain) params.append('domain', filters.domain)
      if (filters.username) params.append('username', filters.username)
      if (filters.browser) params.append('browser', filters.browser)
      if (filters.tld) params.append('tld', filters.tld)
      if (filters.stealer_name) params.append('stealer_name', filters.stealer_name)
      params.append('limit', '10000') // Export up to 10k results
      
      // Fetch from export endpoint
      const response = await fetch(`http://localhost:8000/api/search/export?${params.toString()}`)
      if (!response.ok) throw new Error('Export failed')
      
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `credentials-${Date.now()}.txt`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Exported to TXT (email:password format)')
    } catch (error) {
      console.error('Export failed:', error)
      toast.error('Export failed')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold text-white mb-2">
          Advanced Search
        </h1>
        <p className="text-dark-400">
          Search through {total.toLocaleString()} credentials with powerful filters
        </p>
      </motion.div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-dark-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search by domain, username, or URL..."
            className="w-full pl-12 pr-32 py-4 bg-dark-800/50 backdrop-blur-xl border border-dark-700/50 rounded-2xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
          />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${
                showFilters 
                  ? 'bg-primary-500 text-white' 
                  : 'bg-dark-700/50 text-dark-300 hover:bg-dark-600/50'
              }`}
            >
              <Filter className="h-4 w-4" />
              Filters
            </button>
            <button
              onClick={() => { setPage(0); handleSearch(); }}
              className="px-6 py-2 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all font-medium"
            >
              Search
            </button>
          </div>
        </div>
      </motion.div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <div className="card bg-dark-800/50 backdrop-blur-xl border border-dark-700/50 p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Advanced Filters</h3>
                <button
                  onClick={clearFilters}
                  className="text-sm text-dark-400 hover:text-white transition-colors flex items-center gap-1"
                >
                  <X className="h-4 w-4" />
                  Clear All
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <Globe className="h-4 w-4 inline mr-1" />
                    Domain
                  </label>
                  <input
                    type="text"
                    value={filters.domain}
                    onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
                    placeholder="e.g., gmail.com"
                    className="w-full px-4 py-2 bg-dark-700/50 border border-dark-600/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <User className="h-4 w-4 inline mr-1" />
                    Username
                  </label>
                  <input
                    type="text"
                    value={filters.username}
                    onChange={(e) => setFilters({ ...filters, username: e.target.value })}
                    placeholder="e.g., john@example.com"
                    className="w-full px-4 py-2 bg-dark-700/50 border border-dark-600/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <Chrome className="h-4 w-4 inline mr-1" />
                    Browser
                  </label>
                  <input
                    type="text"
                    value={filters.browser}
                    onChange={(e) => setFilters({ ...filters, browser: e.target.value })}
                    placeholder="e.g., Chrome"
                    className="w-full px-4 py-2 bg-dark-700/50 border border-dark-600/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <Globe className="h-4 w-4 inline mr-1" />
                    TLD
                  </label>
                  <input
                    type="text"
                    value={filters.tld}
                    onChange={(e) => setFilters({ ...filters, tld: e.target.value })}
                    placeholder="e.g., com"
                    className="w-full px-4 py-2 bg-dark-700/50 border border-dark-600/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <Shield className="h-4 w-4 inline mr-1" />
                    Stealer Name
                  </label>
                  <input
                    type="text"
                    value={filters.stealer_name}
                    onChange={(e) => setFilters({ ...filters, stealer_name: e.target.value })}
                    placeholder="e.g., RedLine"
                    className="w-full px-4 py-2 bg-dark-700/50 border border-dark-600/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Header */}
      {credentials.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-between mb-6"
        >
          <div className="text-dark-300">
            Found <span className="text-white font-bold">{total.toLocaleString()}</span> results
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowPasswords(!showPasswords)}
              className="px-4 py-2 bg-dark-700/50 hover:bg-dark-600/50 text-dark-300 rounded-xl transition-all flex items-center gap-2"
            >
              {showPasswords ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showPasswords ? 'Hide' : 'Show'} Passwords
            </button>
            
            <button
              onClick={exportTxt}
              className="px-4 py-2 bg-primary-600/20 hover:bg-primary-600/30 text-primary-400 border border-primary-500/30 rounded-xl transition-all flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export TXT
            </button>
            
            <button
              onClick={exportResults}
              className="px-4 py-2 bg-dark-700/50 hover:bg-dark-600/50 text-dark-300 rounded-xl transition-all flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </motion.div>
      )}

      {/* Results Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <Search className="h-12 w-12 text-primary-500" />
          </motion.div>
        </div>
      ) : credentials.length > 0 ? (
        <div className="space-y-4">
          {credentials.map((credential, index) => (
            <motion.div
              key={credential.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <CredentialCard credential={credential} showPassword={showPasswords} showDeviceLink={true} />
            </motion.div>
          ))}
          
          {/* Pagination */}
          {total > 50 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="px-4 py-2 bg-dark-700/50 hover:bg-dark-600/50 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all"
              >
                Previous
              </button>
              
              <span className="text-dark-300">
                Page {page + 1} of {Math.ceil(total / 50)}
              </span>
              
              <button
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * 50 >= total}
                className="px-4 py-2 bg-dark-700/50 hover:bg-dark-600/50 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all"
              >
                Next
              </button>
            </div>
          )}
        </div>
      ) : searchQuery || Object.values(filters).some(v => v) ? (
        <div className="text-center py-20">
          <Search className="h-16 w-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
          <p className="text-dark-400">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="text-center py-20">
          <Search className="h-16 w-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Start searching</h3>
          <p className="text-dark-400">Enter a search query or use filters to find credentials</p>
        </div>
      )}
    </div>
  )
}
