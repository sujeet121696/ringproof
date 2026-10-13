import { useEffect, useId, useRef, useState } from 'react'
import { applyTheme, readTheme, type Theme } from '../theme'
import { useInstall } from '../useInstall'
import { AutoIcon, GearIcon, InstallIcon, MoonIcon, SunIcon } from './icons'

const THEMES = [
  { id: 'system', label: 'Auto', Icon: AutoIcon },
  { id: 'light', label: 'Light', Icon: SunIcon },
  { id: 'dark', label: 'Dark', Icon: MoonIcon },
] as const

// App settings behind one gear button (a disclosure: button + panel it shows or hides).
// Each setting is its own <section>, so new ones (language, notifications) are added here
// without touching the header.
export function SettingsMenu() {
  const [open, setOpen] = useState(false)
  const [theme, setTheme] = useState<Theme>(readTheme)
  const [iosHint, setIosHint] = useState(false)
  const { way, install } = useInstall()
  const root = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const panelId = useId()

  // Close on a tap or click outside, or on Escape (focus goes back to the gear).
  useEffect(() => {
    if (!open) return
    const onPointer = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      setOpen(false)
      button.current?.focus()
    }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  function chooseTheme(t: Theme) {
    setTheme(t)
    applyTheme(t)
  }

  async function onInstall() {
    if (way === 'ios') {
      setIosHint(!iosHint) // iPhone: show how to add it from the Share menu
    } else {
      await install()
      setOpen(false)
    }
  }

  return (
    <div className="settings" ref={root}>
      <button ref={button} className="icon-btn" aria-label="Settings" aria-expanded={open}
        aria-controls={panelId} onClick={() => setOpen(!open)}>
        <GearIcon size={20} />
      </button>

      {open && (
        <div id={panelId} className="settings-panel" role="group" aria-label="Settings">
          <section>
            <h3>Theme</h3>
            <div className="segmented icons" role="group" aria-label="Theme">
              {THEMES.map(({ id, label, Icon }) => (
                <button key={id} className={theme === id ? 'on' : ''} aria-pressed={theme === id}
                  aria-label={label} title={label} onClick={() => chooseTheme(id)}>
                  <Icon size={20} />
                </button>
              ))}
            </div>
          </section>

          {way && (
            <section>
              <h3>App</h3>
              <button className="menu-item" aria-expanded={way === 'ios' ? iosHint : undefined}
                onClick={onInstall}>
                <InstallIcon size={16} /> Install on this device
              </button>
              {way === 'ios' && iosHint && (
                <p className="muted hint" role="note">Tap <b>Share</b>, then <b>Add to Home Screen</b>.</p>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  )
}
