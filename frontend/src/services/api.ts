import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Credential {
  id: number
  url?: string
  domain?: string
  tld?: string
  username?: string
  password?: string
  browser?: string
  file_path?: string
  device_id?: string
  stealer_name?: string
  created_at: string
}

export interface System {
  id: number
  machine_id?: string
  computer_name?: string
  hardware_id?: string
  machine_user?: string
  ip_address?: string
  country?: string
  log_date?: string
  upload_id: string
  created_at: string
}

export interface Statistics {
  total_credentials: number
  total_systems: number
  total_uploads: number
  unique_domains: number
  unique_countries: number
  unique_stealers: number
}

export interface DomainStatistic {
  domain: string
  count: number
}

export interface CountryStatistic {
  country: string
  count: number
}

export interface StealerStatistic {
  stealer_name: string
  count: number
}

export interface UploadResponse {
  message: string
  filename: string
  task_id: string
  status: string
}

// API Functions
export const fetchStatistics = async (): Promise<Statistics> => {
  const response = await api.get('/stats')
  return response.data
}

export const fetchDomainStats = async (limit = 20): Promise<DomainStatistic[]> => {
  const response = await api.get(`/stats/domains?limit=${limit}`)
  return response.data
}

export const fetchCountryStats = async (limit = 20): Promise<CountryStatistic[]> => {
  const response = await api.get(`/stats/countries?limit=${limit}`)
  return response.data
}

export const fetchStealerStats = async (limit = 20): Promise<StealerStatistic[]> => {
  const response = await api.get(`/stats/stealers?limit=${limit}`)
  return response.data
}

export interface SearchResponse<T> {
  results: T[]
  total: number
  limit: number
  offset: number
}

export const searchCredentials = async (params: {
  q?: string
  domain?: string
  username?: string
  browser?: string
  tld?: string
  limit?: number
  offset?: number
}): Promise<SearchResponse<Credential>> => {
  const response = await api.get('/search/credentials', { params })
  return response.data
}

export const searchSystems = async (params: {
  q?: string
  country?: string
  ip_address?: string
  computer_name?: string
  limit?: number
  offset?: number
}): Promise<SearchResponse<System>> => {
  const response = await api.get('/search/systems', { params })
  return response.data
}

// New Device endpoints
export interface Device {
  id: number
  device_id: string
  device_name: string
  hostname?: string
  upload_batch: string
  total_files: number
  total_credentials: number
  total_domains: number
  total_urls: number
  created_at: string
}

export const fetchDevices = async (params: {
  q?: string
  limit?: number
  offset?: number
}): Promise<SearchResponse<Device>> => {
  const response = await api.get('/devices', { params })
  return response.data
}

export const fetchDevice = async (deviceId: number): Promise<Device> => {
  const response = await api.get(`/devices/${deviceId}`)
  return response.data
}

export const fetchDeviceCredentials = async (
  deviceId: number,
  params: { limit?: number; offset?: number }
): Promise<SearchResponse<Credential>> => {
  const response = await api.get(`/devices/${deviceId}/credentials`, { params })
  return response.data
}

// New statistics endpoints
export const fetchBrowserStats = async (limit = 20) => {
  const response = await api.get(`/stats/browsers?limit=${limit}`)
  return response.data
}
export const fetchTldStats = async (limit = 20) => {
  const response = await api.get(`/stats/tlds?limit=${limit}`)
  return response.data
}

export const fetchPasswordStats = async (limit: number = 20) => {
  const response = await fetch(`${API_BASE_URL}/stats/passwords?limit=${limit}`)
  if (!response.ok) throw new Error('Failed to fetch password stats')
  return response.json()
}

export const fetchSoftwareStats = async (limit = 20) => {
  const response = await api.get(`/stats/software?limit=${limit}`)
  return response.data
}

export default api
