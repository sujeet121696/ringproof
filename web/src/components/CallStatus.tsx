import { mmss } from '../format'
import type { CallState } from '../useCall'

// Live / ended, which call, and how far through it is, by the latest line's time in the call. A call
// played to the end reaches 100% by itself; a stopped one shows where it stopped.
export function CallStatus(props: { state: CallState }) {
  const { status, title, duration, turns } = props.state
  const at = turns.at(-1)?.t ?? 0
  const live = status === 'live'
  const pct = duration > 0 ? Math.min(100, (at / duration) * 100) : 0

  return (
    <section className={`call-status ${status}`} aria-label="Call status">
      <span className="dot" aria-hidden="true" />
      <div className="call-status-text">
        <strong>{live ? 'Live call' : 'Call ended'}</strong>
        <span className="muted">{live ? title : `${title} · nothing was stored`}</span>
      </div>
      <div className="progress" role="progressbar" aria-label="Call progress"
        aria-valuemin={0} aria-valuemax={Math.round(duration)} aria-valuenow={Math.round(at)}>
        <span style={{ width: `${pct}%` }} />
      </div>
      <span className="clock">{mmss(at)} / {mmss(duration)}</span>
    </section>
  )
}
