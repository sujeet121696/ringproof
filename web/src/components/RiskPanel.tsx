import { SIGNAL_LABELS, type RiskResult, type Signal, type SignalType } from '../types'

const LEVEL_TEXT = { low: 'Low risk', medium: 'Be careful', high: 'High risk' } as const
const ALL_SIGNALS = Object.keys(SIGNAL_LABELS) as SignalType[]

export function RiskMeter(props: { risk: RiskResult | null; checking: boolean; live: boolean }) {
  const level = props.risk?.score
  return (
    <section className={`card risk ${level ?? 'none'}`} aria-live="polite">
      <div className="risk-head">
        <h2>Risk</h2>
        {props.checking && <span className="checking">checking…</span>}
      </div>
      <div className="meter" role="meter" aria-valuemin={0} aria-valuemax={2}
        aria-valuenow={level ? ['low', 'medium', 'high'].indexOf(level) : 0}
        aria-valuetext={level ? LEVEL_TEXT[level] : 'Not assessed yet'}>
        {(['low', 'medium', 'high'] as const).map((l) => (
          <span key={l} className={`seg ${l} ${level === l ? 'on' : ''}`} />
        ))}
      </div>
      <p className="level">{level ? LEVEL_TEXT[level] : props.live ? 'Listening…' : 'No call yet'}</p>
      {props.risk && <p className="why">{props.risk.rationale}</p>}
    </section>
  )
}

export function Signals(props: { signals: Signal[] }) {
  return (
    <section className="card signals">
      <h2>Warning signs</h2>
      <ul>
        {ALL_SIGNALS.map((type) => {
          const hit = props.signals.find((s) => s.type === type)
          return (
            <li key={type} className={hit ? 'lit' : ''}>
              <span className="mark" aria-hidden="true">{hit ? '!' : '·'}</span>
              <div>
                <strong>{SIGNAL_LABELS[type]}</strong>
                {hit ? <q>{hit.quote}</q> : <span className="muted"> not heard</span>}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
