import { useEffect, useState } from 'react'
import { useCall } from '../useCall'
import type { FamilyMemory } from '../types'
import { ActionPanel, OfficialCheck } from './ActionPanel'
import { CallerCard } from './CallerCard'
import { RiskMeter, Signals } from './RiskPanel'
import { Transcript } from './Transcript'

type Sample = { id: string; title: string }

export function CallView(props: { memory: FamilyMemory }) {
  const { state, start, stop } = useCall(props.memory)
  const [samples, setSamples] = useState<Sample[]>([])
  const [sampleId, setSampleId] = useState('')
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    fetch('/api/samples')
      .then((r) => r.json())
      .then((list: Sample[]) => {
        setSamples(list)
        setSampleId((id) => id || list[0]?.id || '')
      })
      .catch(() => setSamples([]))
  }, [])

  const live = state.status === 'live'

  return (
    <>
      <form className="controls" onSubmit={(e) => { e.preventDefault(); if (live) stop(); else start(sampleId, speed) }}>
        <label>
          Sample call
          <select value={sampleId} onChange={(e) => setSampleId(e.target.value)} disabled={live}>
            {samples.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
        </label>
        <label>
          Speed
          <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))} disabled={live}>
            <option value={1}>Real time</option>
            <option value={2}>2×</option>
            <option value={4}>4×</option>
          </select>
        </label>
        <button type="submit" className={live ? 'stop' : 'go'} disabled={!sampleId}>
          {live ? 'Stop call' : state.status === 'ended' ? 'Play again' : 'Play call'}
        </button>
        {state.status === 'ended' && <span className="muted ended">Call ended. Nothing was stored.</span>}
        {state.error && <span className="error">{state.error}</span>}
      </form>

      {state.status === 'idle' ? (
        <section className="card empty">
          <h2>Pick a sample call and press Play</h2>
          <p className="muted">
            Ringproof listens as the call plays, checks it against what it remembers about the
            family, and tells {props.memory.user.called} exactly what to do if something is wrong.
          </p>
        </section>
      ) : (
        <div className="call-grid">
          <Transcript turns={state.turns} signals={state.signals} userName={props.memory.user.called} />
          <div className="side">
            <RiskMeter risk={state.risk} checking={state.checking} live={live} />
            <ActionPanel actions={state.actions} challenge={state.challenge} memory={props.memory} />
            <CallerCard risk={state.risk} signals={state.signals} withProfile={state.withProfile} memory={props.memory} />
            <OfficialCheck actions={state.actions} />
            <Signals signals={state.signals} />
          </div>
        </div>
      )}
    </>
  )
}
