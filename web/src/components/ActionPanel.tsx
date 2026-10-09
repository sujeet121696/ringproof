import type { CallState } from '../useCall'
import type { Action, FamilyMemory, Lookup, Notified } from '../types'
import { AlertIcon, CheckIcon } from './icons'

// One line per message: "sent" only after the server confirms it went out.
function sentLine(n: Notified | undefined, who: string, pending: string) {
  if (!n) return pending
  return n.ok ? `Email sent to ${who}.` : `Could not email ${who}: ${n.reason}.`
}

// The intervention is the climax of the demo: one clear instruction, big.
export function ActionPanel(props: { state: CallState; memory: FamilyMemory }) {
  const { actions, challenge: c, notified, checkAnswer } = props.state
  const main = [...actions].reverse().find((a) => a.kind !== 'alert_guardian')
  const alert = actions.find((a) => a.kind === 'alert_guardian')
  const name = (id: string | null) => props.memory.contacts.find((x) => x.id === id)?.name ?? 'the caller'

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
  if (main.kind === 'is_this_you_check') {
    const who = name(main.target)
    if (checkAnswer === 'yes') {
      tone = 'low'
      headline = `The real ${who} confirmed: it is them calling.`
    } else if (checkAnswer === 'no') {
      headline = `The real ${who} says it is not them. This is a scam. Hang up.`
    } else if (notified.is_this_you_check?.ok === false) {
      // The check could not go out, so don't promise one: give the safe instruction instead.
      headline = `Do not send anything. Hang up and call ${who} back on their usual number.`
      detail = sentLine(notified.is_this_you_check, who, '')
    } else {
      const n = notified.is_this_you_check
      detail = sentLine(n, who, `Emailing ${who}…`) + (n ? ' Waiting for their answer.' : '')
    }
  }

  return (
    // A new key when the instruction changes, so the card animates in again and draws the eye.
    <section key={headline} className={`card action ${tone}`} role="alert">
      <h2>What to do</h2>
      <div className="headline-row">
        <span className="action-icon">{tone === 'low' ? <CheckIcon size={28} /> : <AlertIcon size={28} />}</span>
        <p className="headline">{headline}</p>
      </div>
      {detail && <p className="detail">{detail}</p>}
      {alert && <p className="alert-line">✉ {sentLine(notified.alert_guardian, name(alert.target), alert.message)}</p>}
    </section>
  )
}

// The number comes only from the verified table (policy.py); official pages come from the lookup.
export function OfficialCheck(props: { actions: Action[]; lookup: Lookup | null }) {
  const helpline = props.actions.find((a) => a.helpline)?.helpline
  const l = props.lookup
  if (!helpline && !l) return null
  return (
    <section className="card official">
      <h2>Official check</h2>
      {helpline && (
        <>
          <p className="number">{helpline.number}</p>
          <p>{helpline.name}</p>
          <a href={helpline.source} target="_blank" rel="noreferrer">
            Source: {new URL(helpline.source).hostname}
          </a>
        </>
      )}
      {l && (
        <div className="org-check">
          <p className="org-head">What official sites say about calls from “{l.org}”</p>
          {!l.ok && <p className="muted">Could not check official sites right now.</p>}
          {l.ok && l.sources.length === 0 && <p className="muted">No official page found for “{l.org}”.</p>}
          <ul>
            {l.sources.map((src) => (
              <li key={src.url}>
                <a href={src.url} target="_blank" rel="noreferrer">{new URL(src.url).hostname}</a>
                {src.snippet && <q>{src.snippet}</q>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
