import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Server, 
  ArrowLeft,
  Key,
  Globe,
  Database,
  Calendar,
  MapPin,
  Activity,
  Eye,
  EyeOff,
  Download,
  Search as SearchIcon,
  FileText,
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  CreditCard as CreditCardIcon
} from 'lucide-react'
import { fetchDevice, fetchDeviceCredentials, fetchDeviceCreditCards } from '@/services/api'
import toast from 'react-hot-toast'
import CredentialCard from '@/components/CredentialCard'
import CreditCardList from '@/components/CreditCardList'
import { getCountryInfo } from '@/utils/countries'

interface Device {
  id: number
  device_id: string
  device_name: string
  hostname?: string
  ip_address?: string
  country?: string
  language?: string
  os_version?: string
  username?: string
  infection_date?: string
  antivirus?: string
  hwid?: string
  upload_batch: string
  total_files: number
  total_credentials: number
  total_domains: number
  total_urls: number
  created_at: string
}

export default function DeviceDetail() {
  const { deviceId } = useParams<{ deviceId: string }>()
  const deviceIdNum = deviceId ? parseInt(deviceId) : 0
  const navigate = useNavigate()
  const [device, setDevice] = useState<Device | null>(null)
  const [credentials, setCredentials] = useState<any[]>([])
  const [creditCards, setCreditCards] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showPasswords, setShowPasswords] = useState(false)
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const [totalCards, setTotalCards] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'credentials' | 'files' | 'creditcards'>('credentials')
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (deviceId) {
      loadDeviceData()
    }
  }, [deviceId, page])

  const loadDeviceData = async () => {
    if (!deviceIdNum) return
    
    try {
      setLoading(true)
      const [deviceData, credsData, cardsData, filesData] = await Promise.all([
        fetchDevice(deviceIdNum),
        fetchDeviceCredentials(deviceIdNum, { limit: 50, offset: page * 50 }),
        fetchDeviceCreditCards(deviceIdNum, { limit: 50, offset: 0 }),
        fetch(`http://localhost:8000/devices/${deviceIdNum}/files?limit=1000`).then(r => r.json())
      ])
      
      setDevice(deviceData)
      setCredentials(credsData.results)
      setTotal(credsData.total)
      setCreditCards(cardsData.results)
      setTotalCards(cardsData.total)
      setFiles(filesData.results || [])
    } catch (error) {
      console.error('Failed to load device:', error)
      toast.error('Failed to load device data')
    } finally {
      setLoading(false)
    }
  }

  const extractCountryCode = (deviceName: string) => {
    const match = deviceName.match(/\[([A-Z]{2})\]/)
    return match ? match[1] : null
  }

  const extractIP = (deviceName: string) => {
    const match = deviceName.match(/\d+\.\d+\.\d+\.\d+/)
    return match ? match[0] : null
  }

  const buildFileTree = (files: any[]) => {
    const tree: any = {}
    
    files.forEach(file => {
      const parts = file.file_path.split('/')
      let current = tree
      
      parts.forEach((part, index) => {
        if (!part) return
        
        if (!current[part]) {
          current[part] = {
            name: part,
            path: parts.slice(0, index + 1).join('/'),
            isDirectory: index < parts.length - 1 || file.is_directory,
            children: {},
            file: index === parts.length - 1 ? file : null
          }
        }
        current = current[part].children
      })
    })
    
    return tree
  }

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFolders(newExpanded)
  }

  const handleFileClick = async (file: any) => {
    if (!file || !file.id) return
    
    try {
      // Fetch file content from backend
      const response = await fetch(`http://localhost:8000/files/${file.id}`)
      const data = await response.json()
      
      const fileName = file.file_name || 'file'
      const fileExt = fileName.split('.').pop()?.toLowerCase()
      
      // Check if file has content or needs to be downloaded
      if (data.content) {
        // Text files - open in new tab
        if (['txt', 'log', 'json', 'xml', 'html', 'css', 'js', 'md'].includes(fileExt || '')) {
          const blob = new Blob([data.content], { type: 'text/plain' })
          const url = URL.createObjectURL(blob)
          window.open(url, '_blank')
          toast.success('File opened in new tab')
        } 
        // PNG/images - open in new tab
        else if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(fileExt || '')) {
          // If content is base64, create image
          const blob = new Blob([data.content], { type: `image/${fileExt}` })
          const url = URL.createObjectURL(blob)
          window.open(url, '_blank')
          toast.success('Image opened in new tab')
        }
        // Other files - download
        else {
          const blob = new Blob([data.content], { type: 'application/octet-stream' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = fileName
          a.click()
          URL.revokeObjectURL(url)
          toast.success('File downloaded')
        }
      } else {
        toast.error('File has no content')
      }
    } catch (error) {
      console.error('Failed to open file:', error)
      toast.error('Failed to open file')
    }
  }

  const renderFileTree = (tree: any, depth = 0) => {
    return Object.values(tree).map((node: any, index) => {
      const hasChildren = Object.keys(node.children).length > 0
      const isExpanded = expandedFolders.has(node.path)
      
      return (
        <div key={node.path || index}>
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.01 }}
            className="flex items-center gap-2 p-2 hover:bg-dark-700/30 rounded-lg cursor-pointer group"
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
            onClick={() => {
              if (hasChildren) {
                toggleFolder(node.path)
              } else if (node.file) {
                handleFileClick(node.file)
              }
            }}
          >
            {hasChildren && (
              <motion.div
                animate={{ rotate: isExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronRight className="h-4 w-4 text-dark-400" />
              </motion.div>
            )}
            
            {!hasChildren && <div className="w-4" />}
            
            {node.isDirectory ? (
              <Folder className="h-4 w-4 text-yellow-400 flex-shrink-0" />
            ) : (
              <FileText className="h-4 w-4 text-blue-400 flex-shrink-0" />
            )}
            
            <span className="text-sm text-white truncate group-hover:text-primary-400 transition-colors">
              {node.name}
            </span>
            
            {node.file && node.file.file_size > 0 && (
              <span className="text-xs text-dark-400 ml-auto">
                {(node.file.file_size / 1024).toFixed(1)} KB
              </span>
            )}
          </motion.div>
          
          {hasChildren && isExpanded && (
            <div>
              {renderFileTree(node.children, depth + 1)}
            </div>
          )}
        </div>
      )
    })
  }

  const exportCredentials = () => {
    const csv = [
      ['Domain', 'URL', 'Username', 'Password', 'Browser', 'TLD'].join(','),
      ...credentials.map(c => [
        c.domain || '',
        c.url || '',
        c.username || '',
        c.password || '',
        c.browser || '',
        c.tld || ''
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${device?.device_name || 'device'}-credentials.csv`
    a.click()
    toast.success('Exported to CSV')
  }

  if (loading && !device) {
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

  if (!device) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-8">
        <div className="text-center py-20">
          <Server className="h-16 w-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Device not found</h3>
          <button
            onClick={() => navigate('/devices')}
            className="text-primary-400 hover:text-primary-300 transition-colors"
          >
            Back to Devices
          </button>
        </div>
      </div>
    )
  }

  const countryCode = extractCountryCode(device.device_name)
  const ipAddress = extractIP(device.device_name)

  const filteredCredentials = searchQuery
    ? credentials.filter(c => 
        c.domain?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.url?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : credentials

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-8">
      {/* Back Button */}
      <motion.button
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        onClick={() => navigate('/devices')}
        className="mb-6 flex items-center gap-2 text-dark-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-5 w-5" />
        Back to Devices
      </motion.button>

      {/* Device Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="card bg-dark-800/50 backdrop-blur-xl border border-dark-700/50 p-8 rounded-2xl">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl">
                <Server className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  {device.hostname || device.device_name}
                </h1>
                {device.hostname && device.hostname !== device.device_name && (
                  <p className="text-sm text-dark-400 mb-2">Folder: {device.device_name}</p>
                )}
                <div className="flex items-center flex-wrap gap-2 mt-1">
                  {device.country && (() => {
                    const countryInfo = getCountryInfo(device.country)
                    return countryInfo && (
                      <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-lg flex items-center gap-1 border border-blue-500/20">
                        <span>{countryInfo.flag}</span>
                        {countryInfo.name}
                      </span>
                    )
                  })()}
                  {device.ip_address && (
                    <span className="px-3 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-lg font-mono border border-purple-500/20">
                      📍 {device.ip_address}
                    </span>
                  )}
                  {device.antivirus && (
                    <span className="px-3 py-1 bg-green-500/10 text-green-400 text-xs rounded-lg border border-green-500/20">
                      🛡️ {device.antivirus}
                    </span>
                  )}
                  {device.infection_date && (
                    <span className="px-3 py-1 bg-red-500/10 text-red-400 text-xs rounded-lg flex items-center gap-1 border border-red-500/20">
                      <Calendar className="h-3 w-3" />
                      Infected: {(() => {
                        // Parse DD.MM.YYYY HH:MM:SS format (European: day/month/year)
                        const parts = device.infection_date.split(' ')[0].split('.')
                        if (parts.length === 3) {
                          const [day, month, year] = parts
                          // Create date with month-1 because JS months are 0-indexed
                          const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
                          return date.toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })
                        }
                        return device.infection_date
                      })()}
                    </span>
                  )}
                  <span className="px-3 py-1 bg-dark-700/50 text-dark-300 text-xs rounded-lg flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Ingested: {new Date(device.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-dark-700/30 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Key className="h-5 w-5 text-blue-400" />
                <span className="text-sm text-dark-400">Credentials</span>
              </div>
              <p className="text-3xl font-bold text-white">{device.total_credentials.toLocaleString()}</p>
            </div>
            
            <div className="p-4 bg-dark-700/30 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="h-5 w-5 text-green-400" />
                <span className="text-sm text-dark-400">Domains</span>
              </div>
              <p className="text-3xl font-bold text-white">{device.total_domains.toLocaleString()}</p>
            </div>
            
            <div className="p-4 bg-dark-700/30 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="h-5 w-5 text-purple-400" />
                <span className="text-sm text-dark-400">URLs</span>
              </div>
              <p className="text-3xl font-bold text-white">{device.total_urls.toLocaleString()}</p>
            </div>
            
            <div className="p-4 bg-dark-700/30 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-5 w-5 text-orange-400" />
                <span className="text-sm text-dark-400">Files</span>
              </div>
              <p className="text-3xl font-bold text-white">{device.total_files.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <div className="flex items-center gap-2 border-b border-dark-700/50">
          <button
            onClick={() => setActiveTab('credentials')}
            className={`px-6 py-3 font-medium transition-all relative ${
              activeTab === 'credentials'
                ? 'text-primary-400'
                : 'text-dark-400 hover:text-white'
            }`}
          >
            <Key className="h-4 w-4 inline mr-2" />
            Credentials ({total})
            {activeTab === 'credentials' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-400"
              />
            )}
          </button>
          
          <button
            onClick={() => setActiveTab('creditcards')}
            className={`px-6 py-3 font-medium transition-all relative ${
              activeTab === 'creditcards'
                ? 'text-primary-400'
                : 'text-dark-400 hover:text-white'
            }`}
          >
            <CreditCardIcon className="h-4 w-4 inline mr-2" />
            Credit Cards ({totalCards})
            {activeTab === 'creditcards' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-400"
              />
            )}
          </button>
          
          <button
            onClick={() => setActiveTab('files')}
            className={`px-6 py-3 font-medium transition-all relative ${
              activeTab === 'files'
                ? 'text-primary-400'
                : 'text-dark-400 hover:text-white'
            }`}
          >
            <Folder className="h-4 w-4 inline mr-2" />
            Files ({files.length})
            {activeTab === 'files' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-400"
              />
            )}
          </button>
        </div>
      </motion.div>

      {/* Search & Actions - Only show for credentials tab */}
      {activeTab === 'credentials' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6 flex items-center gap-4"
        >
          <div className="flex-1 relative">
            <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-dark-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search credentials..."
              className="w-full pl-12 pr-4 py-3 bg-dark-800/50 backdrop-blur-xl border border-dark-700/50 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 transition-all"
            />
          </div>
          
          <button
            onClick={() => setShowPasswords(!showPasswords)}
            className="px-4 py-3 bg-dark-700/50 hover:bg-dark-600/50 text-dark-300 rounded-xl transition-all flex items-center gap-2"
          >
            {showPasswords ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            {showPasswords ? 'Hide' : 'Show'}
          </button>
          
          <button
            onClick={exportCredentials}
            className="px-4 py-3 bg-dark-700/50 hover:bg-dark-600/50 text-dark-300 rounded-xl transition-all flex items-center gap-2"
          >
            <Download className="h-5 w-5" />
            Export
          </button>
        </motion.div>
      )}

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'credentials' ? (
          <motion.div
            key="credentials"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-4"
          >
            {filteredCredentials.length > 0 ? (
              filteredCredentials.map((credential, index) => (
                <motion.div
                  key={credential.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.02 }}
                >
                  <CredentialCard credential={credential} showPassword={showPasswords} />
                </motion.div>
              ))
            ) : (
              <div className="text-center py-20">
                <SearchIcon className="h-16 w-16 text-dark-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No credentials found</h3>
                <p className="text-dark-400">Try adjusting your search</p>
              </div>
            )}
          </motion.div>
        ) : activeTab === 'creditcards' ? (
          <motion.div
            key="creditcards"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            <CreditCardList cards={creditCards} isLoading={loading} />
          </motion.div>
        ) : (
          <motion.div
            key="files"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {files.length > 0 ? (
              <div className="card bg-dark-800/30 border border-dark-700/50 rounded-xl p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-dark-400">File Tree</h3>
                  <button
                    onClick={() => setExpandedFolders(new Set())}
                    className="text-xs text-dark-400 hover:text-white transition-colors"
                  >
                    Collapse All
                  </button>
                </div>
                <div className="space-y-1">
                  {renderFileTree(buildFileTree(files))}
                </div>
              </div>
            ) : (
              <div className="text-center py-20">
                <Folder className="h-16 w-16 text-dark-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No files found</h3>
                <p className="text-dark-400">This device has no stored files</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pagination */}
      {total > 50 && !searchQuery && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-6 py-3 bg-dark-700/50 hover:bg-dark-600/50 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all font-medium"
          >
            Previous
          </button>
          
          <span className="text-dark-300 px-4">
            Page {page + 1} of {Math.ceil(total / 50)}
          </span>
          
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * 50 >= total}
            className="px-6 py-3 bg-dark-700/50 hover:bg-dark-600/50 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all font-medium"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
