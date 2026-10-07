import { useEffect, useState } from 'react'

type Health = { status: string; provider: string }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setHealth)
      .catch(() => setError(true))
  }, [])

  return (
    <main className="shell">
      <img src="/logo.svg" alt="Ringproof" width="240" />
      <p>Dashboard coming soon.</p>
      <p>
        Backend:{' '}
        {health
          ? `connected (brain: ${health.provider})`
          : error
            ? 'not reachable. Is uvicorn running on :8100?'
            : 'checking...'}
      </p>
    </main>
  )
}

export default App
