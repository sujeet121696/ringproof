import { useEffect, useState } from 'react'

// Chrome/Edge/Android fire this when the app can be installed; not in the DOM lib types yet.
type InstallPrompt = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> }

const standalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as Navigator & { standalone?: boolean }).standalone === true

// iPhone/iPad Safari has no install prompt: the user adds it from the Share menu.
const ios = () => /iphone|ipad|ipod/i.test(navigator.userAgent)

export function InstallButton() {
  const [prompt, setPrompt] = useState<InstallPrompt | null>(null)
  const [installed, setInstalled] = useState(standalone)
  const [hint, setHint] = useState(false)

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault() // show our button instead of the browser's mini-bar
      setPrompt(e as InstallPrompt)
    }
    const onInstalled = () => { setInstalled(true); setPrompt(null) }
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  if (installed) return null

  if (prompt) {
    return (
      <button className="install" onClick={async () => {
        await prompt.prompt()
        await prompt.userChoice
        setPrompt(null) // a prompt can be used once
      }}>Install app</button>
    )
  }

  if (ios()) {
    return (
      <span className="install-wrap">
        <button className="install" aria-expanded={hint} onClick={() => setHint(!hint)}>Install app</button>
        {hint && <span className="install-hint" role="note">Tap <b>Share</b>, then <b>Add to Home Screen</b>.</span>}
      </span>
    )
  }

  return null
}
