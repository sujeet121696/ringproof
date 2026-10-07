import { useEffect, useState } from 'react'
import { CallView } from './components/CallView'
import { InstallButton } from './components/InstallButton'
import { MemoryView } from './components/MemoryView'
import { loadOrSeed, saveMemory } from './memory'
import type { FamilyMemory } from './types'
import './App.css'

type Theme = 'system' | 'light' | 'dark'

function readTheme(): Theme {
  try {
    const t = localStorage.getItem('theme')
    return t === 'light' || t === 'dark' ? t : 'system'
  } catch {
    return 'system'
  }
}

// Same mechanism as kharidwise: data-theme on <html>, saved choice applied before paint by theme-init.js.
function applyTheme(t: Theme) {
  if (t === 'system') delete document.documentElement.dataset.theme
  else document.documentElement.dataset.theme = t
  try {
    if (t === 'system') localStorage.removeItem('theme')
    else localStorage.setItem('theme', t)
  } catch {
    /* storage blocked: the choice just won't persist */
  }
}

function App() {
  const [memory, setMemory] = useState<FamilyMemory | null>(null)
  const [failed, setFailed] = useState(false)
  const [saveFailed, setSaveFailed] = useState(false)
  const [tab, setTab] = useState<'call' | 'memory'>('call')
  const [theme, setTheme] = useState<Theme>(readTheme)

  useEffect(() => {
    loadOrSeed().then(setMemory).catch(() => setFailed(true))
  }, [])

  // Every edit is saved to this browser straight away.
  function updateMemory(m: FamilyMemory) {
    setMemory(m)
    saveMemory(m).then(() => setSaveFailed(false), () => setSaveFailed(true))
  }

  return (
    <>
      <header className="site-head">
        {/* Mark + text wordmark, as kharidwise does (kharid<b>wise</b>), so it follows the app's theme. */}
        <a className="brand" href="/" aria-label="Ringproof home">
          <img src="/logo-mark.svg" alt="" width="34" height="34" />
          <span className="word">Ring<b>proof</b></span>
        </a>
        <nav className="tabs" aria-label="Views">
          <button className={tab === 'call' ? 'on' : ''} onClick={() => setTab('call')}>Call</button>
          <button className={tab === 'memory' ? 'on' : ''} onClick={() => setTab('memory')}>Family memory</button>
        </nav>
        <InstallButton />
        <div className="theme" role="group" aria-label="Theme">
          {(['system', 'light', 'dark'] as const).map((t) => (
            <button key={t} className={theme === t ? 'on' : ''} aria-pressed={theme === t}
              onClick={() => { setTheme(t); applyTheme(t) }}>
              {t === 'system' ? 'Auto' : t === 'light' ? 'Light' : 'Dark'}
            </button>
          ))}
        </div>
      </header>

      <main className="page">
        {failed && <p className="error">Could not reach the Ringproof backend. Is it running on port 8100?</p>}
        {saveFailed && <p className="error">Could not save to this browser's storage. Changes will be lost on reload.</p>}
        {!memory && !failed && <p className="muted">Loading family memory…</p>}
        {memory && tab === 'call' && <CallView memory={memory} />}
        {memory && tab === 'memory' && <MemoryView memory={memory} onChange={updateMemory} />}
      </main>
    </>
  )
}

export default App
