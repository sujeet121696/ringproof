import { useEffect, useState } from 'react'
import { CallView } from './components/CallView'
import { MemoryView } from './components/MemoryView'
import { PrivacyView } from './components/PrivacyView'
import { SettingsMenu } from './components/SettingsMenu'
import { loadOrSeed, saveMemory } from './memory'
import type { FamilyMemory } from './types'
import './App.css'

function App() {
  const [memory, setMemory] = useState<FamilyMemory | null>(null)
  const [failed, setFailed] = useState(false)
  const [saveFailed, setSaveFailed] = useState(false)
  const [tab, setTab] = useState<'call' | 'memory' | 'privacy'>('call')

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
        <SettingsMenu />
      </header>

      <main className="page">
        {failed && <p className="error">Could not reach the Ringproof backend. Is it running on port 8100?</p>}
        {saveFailed && <p className="error">Could not save to this browser's storage. Changes will be lost on reload.</p>}
        {!memory && !failed && tab !== 'privacy' && <p className="muted">Loading family memory…</p>}
        {memory && tab === 'call' && <CallView memory={memory} />}
        {memory && tab === 'memory' && <MemoryView memory={memory} onChange={updateMemory} />}
        {tab === 'privacy' && <PrivacyView />}
      </main>

      <footer className="site-foot">
        <button className="link" onClick={() => { setTab('privacy'); window.scrollTo(0, 0) }}>Privacy and terms</button>
        <span aria-hidden="true">·</span>
        <a href="https://github.com/sujeet121696/ringproof" target="_blank" rel="noreferrer">Source on GitHub</a>
      </footer>
    </>
  )
}

export default App
