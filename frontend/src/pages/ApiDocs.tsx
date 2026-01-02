import React, { useState, useEffect } from 'react';

// This is a new, self-contained, and functional API Docs page.

// Helper component for stat cards
function SimpleStatCard({ title, value, icon }: { title: string, value: string | number, icon: string }) {
  return (
    <div style={styles.statCard}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ fontSize: '1.5rem' }}>{icon}</div>
        <div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{title}</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'white' }}>{value}</div>
        </div>
      </div>
    </div>
  );
}

// Helper component for endpoint display
function EndpointCard({ method, path, description, example, response }: any) {
  const [copied, setCopied] = useState<'request' | 'response' | null>(null);

  const handleCopy = (text: string, type: 'request' | 'response') => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div style={styles.card}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <span style={{ ...styles.method, background: method === 'GET' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)', color: method === 'GET' ? '#10b981' : '#3b82f6' }}>
          {method}
        </span>
        <code style={styles.path}>{path}</code>
      </div>
      <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>{description}</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
        <div>
          <h4 style={styles.subheading}>Example Request</h4>
          <div style={styles.codeContainer}>
            <pre style={styles.code}><code style={{whiteSpace: 'pre-wrap'}}>{example}</code></pre>
            <button onClick={() => handleCopy(example, 'request')} style={styles.copyButton}>
              {copied === 'request' ? '✅' : '📋'}
            </button>
          </div>
        </div>
        <div>
          <h4 style={styles.subheading}>Example Response</h4>
          <div style={styles.codeContainer}>
            <pre style={styles.code}><code style={{whiteSpace: 'pre-wrap'}}>{response}</code></pre>
            <button onClick={() => handleCopy(response, 'response')} style={styles.copyButton}>
              {copied === 'response' ? '✅' : '📋'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main API Docs Component
export default function ApiDocs() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/stats')
      .then(res => res.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const endpoints = [
    {
      method: 'GET',
      path: '/api/stats',
      description: 'Get overall database statistics.',
      example: 'curl http://localhost:8000/api/stats',
      response: JSON.stringify({ total_credentials: 46346, total_systems: 110, unique_domains: 2847, unique_stealers: 1989 }, null, 2)
    },
    {
      method: 'GET',
      path: '/api/search/credentials?q=...',
      description: 'Search for credentials with a query string. Supports advanced queries like `domain:google.com`.',
      example: 'curl "http://localhost:8000/api/search/credentials?q=domain:gmail.com&limit=1"',
      response: JSON.stringify({ results: [{ id: 1, username: 'test', password: 'password123', domain: 'gmail.com' }], total: 1, limit: 1, offset: 0 }, null, 2)
    },
    {
      method: 'GET',
      path: '/api/devices',
      description: 'Get list of all devices with pagination.',
      example: 'curl "http://localhost:8000/api/devices?limit=10&offset=0"',
      response: JSON.stringify({ results: [{ id: 1, device_id: "abc123", device_name: "PC-001", hostname: "DESKTOP-ABC" }], total: 1, limit: 10, offset: 0 }, null, 2)
    },
    {
      method: 'GET',
      path: '/api/wallets',
      description: 'Get list of all cryptocurrency wallets found.',
      example: 'curl "http://localhost:8000/api/wallets?limit=10"',
      response: JSON.stringify([{ id: 1, wallet_type: "ETH", address: "0x...", has_balance: false }], null, 2)
    },
    {
      method: 'GET',
      path: '/api/credit-cards',
      description: 'Get list of all credit cards found.',
      example: 'curl "http://localhost:8000/api/credit-cards?limit=10"',
      response: JSON.stringify({ results: [{ id: 1, card_number_masked: "****1234", card_brand: "Visa" }], total: 1, limit: 10, offset: 0 }, null, 2)
    },
    {
      method: 'GET',
      path: '/api/stats/domains',
      description: 'Get top domains by credential count.',
      example: 'curl "http://localhost:8000/api/stats/domains?limit=10"',
      response: JSON.stringify([{ domain: "google.com", count: 1234 }, { domain: "facebook.com", count: 987 }], null, 2)
    }
  ];

  return (
    <div style={styles.pageContainer}>
      <div style={styles.contentWrapper}>
        <div style={{ marginBottom: '3rem' }}>
          <h1 style={styles.header}>API Documentation</h1>
          <p style={styles.subHeader}>RESTful API for the Snatchbase Intelligence Platform.</p>
        </div>

        <div style={styles.statsGrid}>
          <SimpleStatCard title="Total Credentials" value={stats ? stats.total_credentials.toLocaleString() : '...'} icon="🔐" />
          <SimpleStatCard title="Infected Systems" value={stats ? stats.total_systems.toLocaleString() : '...'} icon="💻" />
          <SimpleStatCard title="Unique Domains" value={stats ? stats.unique_domains.toLocaleString() : '...'} icon="🌐" />
          <SimpleStatCard title="API Endpoints" value="29" icon="🔌" />
        </div>

        <div style={styles.sectionContainer}>
          <h2 style={styles.sectionTitle}>Interactive API Explorer</h2>
          <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>For detailed, interactive documentation, please visit the Swagger UI:</p>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={styles.swaggerLink}>
            http://localhost:8000/docs
          </a>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {endpoints.map(ep => <EndpointCard key={ep.path} {...ep} />)}
        </div>
      </div>
    </div>
  );
}

// --- Styles ---
const styles: { [key: string]: React.CSSProperties } = {
  pageContainer: {
    minHeight: '100vh',
    padding: '2rem',
    color: 'white',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    background: '#0f172a'
  },
  contentWrapper: {
    maxWidth: '80rem',
    margin: '0 auto'
  },
  header: {
    fontSize: '3rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%)',
    WebkitBackgroundClip: 'text',
    // @ts-ignore
    WebkitTextFillColor: 'transparent'
  },
  subHeader: {
    fontSize: '1.125rem',
    color: '#94a3b8',
    marginBottom: '2rem'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '3rem'
  },
  statCard: {
    background: 'rgba(30, 41, 59, 0.5)',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: '1rem',
    padding: '1.5rem'
  },
  sectionContainer: {
    background: 'rgba(30, 41, 59, 0.5)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: '1rem',
    padding: '2rem',
    marginBottom: '2rem'
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1.5rem'
  },
  swaggerLink: {
    display: 'inline-block',
    background: '#3b82f6',
    color: 'white',
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    textDecoration: 'none',
    fontWeight: '500'
  },
  card: {
    background: 'rgba(30, 41, 59, 0.5)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: '1rem',
    padding: '1.5rem'
  },
  method: {
    padding: '0.25rem 0.75rem',
    borderRadius: '0.25rem',
    fontSize: '0.75rem',
    fontWeight: 'bold'
  },
  path: {
    color: '#3b82f6',
    fontSize: '1.125rem',
    fontFamily: 'monospace'
  },
  subheading: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#d1d5db',
    marginBottom: '0.5rem'
  },
  codeContainer: {
    background: 'rgba(15, 23, 42, 0.8)',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: '0.5rem',
    padding: '1rem',
    position: 'relative'
  },
  code: {
    fontSize: '0.875rem',
    color: '#d1d5db',
    margin: 0,
    overflowX: 'auto'
  },
  copyButton: {
    position: 'absolute',
    top: '0.5rem',
    right: '0.5rem',
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '0.25rem',
    padding: '0.25rem',
    cursor: 'pointer',
    color: '#94a3b8'
  }
};
