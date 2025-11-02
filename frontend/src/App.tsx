import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import DashboardSimple from './pages/DashboardSimple'
import SearchNew from './pages/SearchNew'
import DevicesPage from './pages/DevicesPage'
import DeviceDetail from './pages/DeviceDetail'
import AnalyticsNew from './pages/AnalyticsNew'
import ApiDocs from './pages/ApiDocs'
import TopDomainsPage from './pages/TopDomainsPage'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <Navbar />
      
      <main className="relative z-10">
        <Routes>
          <Route path="/" element={<DashboardSimple />} />
          <Route path="/search" element={<SearchNew />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/device/:deviceId" element={<DeviceDetail />} />
          <Route path="/analytics" element={<AnalyticsNew />} />
          <Route path="/topdomains" element={<TopDomainsPage />} />
          <Route path="/api" element={<ApiDocs />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
