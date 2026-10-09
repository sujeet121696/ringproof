// Light/dark theme. Same mechanism as kharidwise: data-theme on <html>, and the saved choice is
// applied before paint by public/theme-init.js. "system" follows the device setting.

export type Theme = 'system' | 'light' | 'dark'

export function readTheme(): Theme {
  try {
    const t = localStorage.getItem('theme')
    return t === 'light' || t === 'dark' ? t : 'system'
  } catch {
    return 'system'
  }
}

export function applyTheme(t: Theme) {
  if (t === 'system') delete document.documentElement.dataset.theme
  else document.documentElement.dataset.theme = t
  try {
    if (t === 'system') localStorage.removeItem('theme')
    else localStorage.setItem('theme', t)
  } catch {
    /* storage blocked: the choice just won't persist */
  }
}
