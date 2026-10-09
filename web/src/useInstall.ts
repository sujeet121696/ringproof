import { useEffect, useState } from 'react'

// Chrome/Edge/Android fire this when the app can be installed; not in the DOM lib types yet.
type InstallPrompt = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> }

const standalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as Navigator & { standalone?: boolean }).standalone === true

// iPhone/iPad Safari has no install prompt: the user adds it from the Share menu.
const ios = () => /iphone|ipad|ipod/i.test(navigator.userAgent)

/** How this browser can install the app: a real prompt, the iPhone Share-menu hint, or not at all. */
export type InstallWay = 'prompt' | 'ios' | null

export function useInstall(): { way: InstallWay; install: () => Promise<void> } {
  const [prompt, setPrompt] = useState<InstallPrompt | null>(null)
  const [installed, setInstalled] = useState(standalone)

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

  async function install() {
    if (!prompt) return
    try {
      await prompt.prompt()
      await prompt.userChoice
    } catch {
      /* the browser refused to show it; nothing to do */
    } finally {
      setPrompt(null) // a prompt can be used once
    }
  }

  const way: InstallWay = installed ? null : prompt ? 'prompt' : ios() ? 'ios' : null
  return { way, install }
}
