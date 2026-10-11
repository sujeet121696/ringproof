import { useEffect, useState } from 'react'
import { useCall } from '../useCall'
import type { FamilyMemory, Turn } from '../types'
import { ActionPanel, OfficialCheck } from './ActionPanel'
import { CallerCard } from './CallerCard'
import { CallStatus } from './CallStatus'
import { FamilyIcon, ListenIcon, ShieldIcon } from './icons'
import { RiskMeter, Signals } from './RiskPanel'
import { Transcript } from './Transcript'

type Sample = { id: string; title: string }
type Mode = 'sample' | 'recording' | 'phone'
// What the server has switched on (/api/health): the speech service, and the phone number.
type Features = { transcription: boolean; phone: string }

const HEADINGS: Record<Mode, string> = {
  sample: 'Pick a sample call and press Play',
  recording: 'Choose a call recording and press Play',
  phone: 'Press Wait for a call, then ring the Ringproof number',
}

export function CallView(props: { memory: FamilyMemory }) {
  const { state, start, stop } = useCall(props.memory)
  const [samples, setSamples] = useState<Sample[]>([])
  const [sampleId, setSampleId] = useState('')
  const [speed, setSpeed] = useState(1)
  const [mode, setMode] = useState<Mode>('sample')
  const [features, setFeatures] = useState<Features>({ transcription: false, phone: '' })
  const [file, setFile] = useState<File | null>(null)
  const [transcribing, setTranscribing] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((h) => setFeatures({ transcription: Boolean(h.transcription), phone: h.phone ?? '' }))
      .catch(() => {})
  }, [])

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
  const waiting = state.status === 'waiting'
  const busy = live || waiting || transcribing
  const called = props.memory.user.called || 'you'

  // The recording goes to the speech service once; its transcript then plays like a sample.
  const playRecording = async (f: File) => {
    setTranscribing(true)
    setUploadError(null)
    try {
      const res = await fetch('/api/transcribe', { method: 'POST', body: f })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(body.detail || 'Transcription failed.')
      start({ turns: body.turns as Turn[], title: f.name }, speed)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Transcription failed.')
    } finally {
      setTranscribing(false)
    }
  }

  const submit = () => {
    setUploadError(null)
    if (live || waiting) stop()
    else if (mode === 'phone') start({ phone: true }, speed)
    else if (mode === 'recording') { if (file) void playRecording(file) }
    else start({ sample_id: sampleId }, speed)
  }

  const ready = mode === 'sample' ? Boolean(sampleId) : mode === 'recording' ? Boolean(file) : true
  const label = live ? 'Stop call' : waiting ? 'Stop waiting' : transcribing ? 'Transcribing…'
    : mode === 'phone' ? 'Wait for a call' : state.status === 'ended' ? 'Play again' : 'Play call'
  const error = uploadError ?? state.error

  return (
    <>
      <form className="controls" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <label>
          Call from
          <select value={mode} onChange={(e) => setMode(e.target.value as Mode)} disabled={busy}>
            <option value="sample">Sample call</option>
            <option value="recording" disabled={!features.transcription}>
              Recording{features.transcription ? '' : ' (not set up)'}
            </option>
            <option value="phone" disabled={!features.phone}>Phone line{features.phone ? '' : ' (not set up)'}</option>
          </select>
        </label>
        {mode === 'sample' && (
          <label>
            Sample call
            <select value={sampleId} onChange={(e) => setSampleId(e.target.value)} disabled={busy}>
              {samples.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
          </label>
        )}
        {mode === 'recording' && (
          <label>
            Recording (caller speaks first)
            <input type="file" accept="audio/*" disabled={busy} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
        )}
        {mode !== 'phone' && (
          <label>
            Speed
            <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))} disabled={busy}>
              <option value={1}>Real time</option>
              <option value={2}>2×</option>
              <option value={4}>4×</option>
            </select>
          </label>
        )}
        <button type="submit" className={live || waiting ? 'stop' : 'go'} disabled={transcribing || (!live && !waiting && !ready)}>
          {label}
        </button>
        {error && <span className="error">{error}</span>}
      </form>

      {waiting ? (
        <section className="card empty" aria-live="polite">
          <h2>Waiting for a call</h2>
          <p className="muted">
            Ring <strong>{state.number}</strong>. The caller hears a short notice, then Ringproof listens and checks
            the call here, line by line.
          </p>
        </section>
      ) : state.status === 'idle' ? (
        <section className="card empty">
          <h2>{HEADINGS[mode]}</h2>
          <ol className="steps">
            <li>
              <span className="step-icon"><ListenIcon size={22} /></span>
              <strong>Listens to the call</strong>
              <span className="muted">Checks it turn by turn as it plays.</span>
            </li>
            <li>
              <span className="step-icon"><FamilyIcon size={22} /></span>
              <strong>Knows the family</strong>
              <span className="muted">Compares the caller with what this browser remembers about them.</span>
            </li>
            <li>
              <span className="step-icon"><ShieldIcon size={22} /></span>
              <strong>Says what to do</strong>
              <span className="muted">
                Tells {called} to ask the code word, waits for the real person to confirm, or says hang up and call 1930.
              </span>
            </li>
          </ol>
        </section>
      ) : (
        <>
          <CallStatus state={state} />
          <div className="call-grid">
            <Transcript turns={state.turns} signals={state.signals} userName={props.memory.user.called || 'You'} live={live} />
            <div className="side">
              <RiskMeter risk={state.risk} checking={state.checking} live={live} />
              <ActionPanel state={state} memory={props.memory} />
              <CallerCard risk={state.risk} signals={state.signals} withProfile={state.withProfile} memory={props.memory} />
              <OfficialCheck actions={state.actions} lookup={state.lookup} />
              <Signals signals={state.signals} />
            </div>
          </div>
        </>
      )}
    </>
  )
}
