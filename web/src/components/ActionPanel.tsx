import type { Challenge } from '../useCall'
import type { Action, FamilyMemory } from '../types'

// The intervention is the climax of the demo: one clear instruction, big.
export function ActionPanel(props: { actions: Action[]; challenge: Challenge | null; memory: FamilyMemory }) {
  const main = [...props.actions].reverse().find((a) => a.kind !== 'alert_guardian')
  const alert = props.actions.find((a) => a.kind === 'alert_guardian')
  const name = (id: string | null) => props.memory.contacts.find((c) => c.id === id)?.name ?? 'the caller'

  if (!main) {
    return (
      <section className="card action idle">
        <h2>What to do</h2>
        <p className="muted">Nothing needed. Ringproof stays quiet on normal calls.</p>
      </section>
    )
  }

  let tone = main.kind === 'watch' ? 'medium' : 'high'
  let headline = main.message
  let detail: string | null = null
  const c = props.challenge
  if (main.kind === 'code_word_challenge' && c) {
    if (c.status === 'passed') {
      tone = 'low'
      headline = `Code word correct. This is really ${name(c.target)}.`
    } else if (c.status === 'failed') {
      headline = `The caller could not give the code word. This is not ${name(c.target)}. Hang up.`
    } else {
      detail = 'Ringproof is listening for the answer. The code word never leaves this device.'
    }
  }

  return (
    <section className={`card action ${tone}`} role="alert">
      <h2>What to do</h2>
      <p className="headline">{headline}</p>
      {detail && <p className="detail">{detail}</p>}
      {alert && <p className="alert-line">✉ {alert.message}</p>}
    </section>
  )
}

export function OfficialCheck(props: { actions: Action[] }) {
  const helpline = props.actions.find((a) => a.helpline)?.helpline
  if (!helpline) return null
  return (
    <section className="card official">
      <h2>Official check</h2>
      <p className="number">{helpline.number}</p>
      <p>{helpline.name}</p>
      <a href={helpline.source} target="_blank" rel="noreferrer">
        Source: {new URL(helpline.source).hostname}
      </a>
    </section>
  )
}
