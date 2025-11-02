import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  Globe, 
  User, 
  Key, 
  Eye, 
  EyeOff, 
  Copy,
  AlertTriangle,
  ExternalLink,
  ChevronDown,
  Server,
  Calendar,
  Chrome
} from 'lucide-react'
import toast from 'react-hot-toast'

interface CredentialCardProps {
  credential: any
  showPassword?: boolean
  showDeviceLink?: boolean
}

export default function CredentialCard({ credential, showPassword = false, showDeviceLink = false }: CredentialCardProps) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(showPassword)
  const [isExpanded, setIsExpanded] = useState(false)
  const navigate = useNavigate()
  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(`${label} copied to clipboard`)
    } catch (err) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSeverityColor = (stealer?: string) => {
    if (!stealer) return 'text-gray-400'
    const stealerLower = stealer.toLowerCase()
    if (stealerLower.includes('redline') || stealerLower.includes('vidar')) {
      return 'text-red-400'
    }
    if (stealerLower.includes('raccoon') || stealerLower.includes('mars')) {
      return 'text-yellow-400'
    }
    return 'text-blue-400'
  }

  const getDomainRisk = (domain?: string) => {
    if (!domain) return null
    const riskDomains = ['paypal', 'amazon', 'google', 'microsoft', 'apple', 'facebook', 'twitter']
    const isHighRisk = riskDomains.some(risk => domain.toLowerCase().includes(risk))
    return isHighRisk ? 'high' : 'low'
  }

  const domainRisk = getDomainRisk(credential.domain)

  return (
    <motion.div
      layout
      className="card group bg-dark-800/30 border border-dark-700/50 rounded-xl hover:border-primary-500/30 transition-all overflow-hidden"
    >
      <div 
        className="flex items-center justify-between gap-4 p-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Domain & URL */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <Globe className="h-4 w-4 text-primary-400 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white truncate">
                {credential.domain || 'Unknown Domain'}
              </h3>
              {domainRisk === 'high' && (
                <AlertTriangle className="h-3 w-3 text-red-400 flex-shrink-0" />
              )}
            </div>
            <p className="text-xs text-dark-400 truncate">
              {credential.url || 'No URL'}
            </p>
          </div>
        </div>

        {/* Username */}
        {credential.username && (
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <User className="h-4 w-4 text-dark-400 flex-shrink-0" />
            <p className="text-sm text-dark-300 truncate">{credential.username}</p>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={(e) => {
                e.stopPropagation()
                copyToClipboard(credential.username!, 'Username')
              }}
              className="text-primary-400 hover:text-primary-300 transition-colors flex-shrink-0"
            >
              <Copy className="h-3 w-3" />
            </motion.button>
          </div>
        )}

        {/* Password */}
        {credential.password && (
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Key className="h-4 w-4 text-dark-400 flex-shrink-0" />
            <p className="text-sm text-dark-300 font-mono truncate">
              {isPasswordVisible ? credential.password : '••••••••'}
            </p>
            <div className="flex items-center gap-1 flex-shrink-0">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={(e) => {
                  e.stopPropagation()
                  setIsPasswordVisible(!isPasswordVisible)
                }}
                className="text-dark-400 hover:text-white transition-colors"
              >
                {isPasswordVisible ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={(e) => {
                  e.stopPropagation()
                  copyToClipboard(credential.password!, 'Password')
                }}
                className="text-primary-400 hover:text-primary-300 transition-colors"
              >
                <Copy className="h-3 w-3" />
              </motion.button>
            </div>
          </div>
        )}

        {/* Stealer, Browser & Date */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {credential.is_duplicate && (
            <span 
              className="px-2 py-1 text-xs rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 truncate max-w-[120px] flex items-center gap-1" 
              title={`This credential appears ${credential.duplicate_count + 1} times in this device`}
            >
              <AlertTriangle className="h-3 w-3" />
              Duplicate x{credential.duplicate_count + 1}
            </span>
          )}
          {credential.stealer_name && (
            <span className="px-2 py-1 text-xs rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 truncate max-w-[120px]" title={credential.stealer_name}>
              {credential.stealer_name}
            </span>
          )}
          {credential.tld && (
            <span className="px-2 py-1 text-xs rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 truncate">
              .{credential.tld}
            </span>
          )}
          {credential.browser && (
            <span className="px-2 py-1 text-xs rounded-lg bg-dark-700/50 text-dark-300 truncate max-w-[120px]" title={credential.browser}>
              {credential.browser}
            </span>
          )}
          <span className="text-xs text-dark-500">
            {formatDate(credential.created_at)}
          </span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-4 w-4 text-dark-400" />
          </motion.div>
        </div>
      </div>

      {/* Expanded Details */}
      <motion.div
        initial={false}
        animate={{ height: isExpanded ? 'auto' : 0, opacity: isExpanded ? 1 : 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="px-4 pb-4 pt-2 border-t border-dark-700/50 space-y-3">
          {/* Full URL */}
          {credential.url && (
            <div className="flex items-start gap-2">
              <ExternalLink className="h-4 w-4 text-dark-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-dark-400 mb-1">Full URL</p>
                <p className="text-sm text-white font-mono break-all">{credential.url}</p>
              </div>
            </div>
          )}

          {/* TLD */}
          {credential.tld && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Top-Level Domain</span>
              <span className="text-sm text-white">.{credential.tld}</span>
            </div>
          )}

          {/* Duplicate Warning */}
          {credential.is_duplicate && credential.duplicate_count > 0 && (
            <div className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-400 mb-1">
                    Duplicate Credential Detected
                  </p>
                  <p className="text-xs text-dark-300">
                    This exact username and password combination appears <strong>{credential.duplicate_count + 1} times</strong> in the same device.
                    This could indicate:
                  </p>
                  <ul className="text-xs text-dark-400 mt-2 space-y-1 ml-4 list-disc">
                    <li>The same credentials saved in multiple browsers</li>
                    <li>Duplicate entries in password files</li>
                    <li>Multiple stealer logs from the same device</li>
                  </ul>
                  {credential.duplicate_ids && credential.duplicate_ids.length > 0 && (
                    <p className="text-xs text-dark-400 mt-2">
                      Duplicate IDs: {credential.duplicate_ids.join(', ')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* File Path */}
          {credential.file_path && (
            <div className="flex items-start gap-2">
              <Server className="h-4 w-4 text-dark-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-dark-400 mb-1">Source File</p>
                <p className="text-xs text-dark-300 font-mono break-all">{credential.file_path}</p>
              </div>
            </div>
          )}

          {/* Device Link */}
          {showDeviceLink && credential.device && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/device/${credential.device.id}`)
              }}
              className="w-full mt-2 px-4 py-2 bg-primary-500/10 hover:bg-primary-500/20 text-primary-400 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              <Server className="h-4 w-4" />
              View Device: {credential.device.hostname || credential.device.device_name}
            </button>
          )}

          {/* Created Date */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-dark-400 flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Added
            </span>
            <span className="text-dark-300">{formatDate(credential.created_at)}</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
