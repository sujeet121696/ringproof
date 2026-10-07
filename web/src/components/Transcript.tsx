import { useEffect, useRef } from 'react'
import { SIGNAL_LABELS, type Signal, type Turn } from '../types'

const norm = (s: string) => s.toLowerCase().replace(/\s+/g, ' ').trim()
const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`

// A line is flagged when a signal's quote comes from it (the model quotes the caller's words).
function signalsFor(turn: Turn, signals: Signal[]): Signal[] {
  if (turn.speaker !== 'caller') return []
  const text = norm(turn.text)
  return signals.filter((s) => {
    const q = norm(s.quote).replace(/^["'“]|["'”]$/g, '')
    return q.length > 3 && (text.includes(q) || q.includes(text))
  })
}

export function Transcript(props: { turns: Turn[]; signals: Signal[]; userName: string }) {
  // Scroll the transcript box itself (not the page) to the newest line.
  const box = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = box.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [props.turns.length])

  return (
    <section ref={box} className="card transcript" aria-label="Live transcript">
      <h2>Live transcript</h2>
      <ol className="lines" aria-live="polite">
        {props.turns.map((turn, i) => {
          const hits = signalsFor(turn, props.signals)
          const types = [...new Set(hits.map((h) => h.type))]
          return (
            <li key={i} className={`line ${turn.speaker} ${types.length ? 'flagged' : ''}`}>
              <div className="who">
                {turn.speaker === 'caller' ? 'Caller' : props.userName}
                <span className="time">{mmss(turn.t)}</span>
              </div>
              <p>{turn.text}</p>
              {types.length > 0 && (
                <div className="tags">
                  {types.map((t) => (
                    <span key={t} className="tag">{SIGNAL_LABELS[t]}</span>
                  ))}
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}
