import { useEffect, useState } from 'react'
import { checkHealth } from './api'
import './index.css'

function App() {
  const [backendStatus, setBackendStatus] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus('connected'))
      .catch((err) => setBackendStatus(err?.message || 'Backend unreachable'))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">QModelGuard</h1>
        <p className="text-gray-600 mb-4">Quantum-Safe ML Model Protection</p>
        <p
          className={`text-sm ${backendStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}
        >
          {backendStatus === null ? 'Checking backend…' : backendStatus === 'connected' ? 'Backend connected' : `Error: ${backendStatus}`}
        </p>
      </div>
    </div>
  )
}

export default App
