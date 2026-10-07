import type { FamilyMemory, RiskResult, Signal } from '../types'

// Shows who the caller claims to be, and the memory Ringproof compares them against.
export function CallerCard(props: {
  risk: RiskResult | null
  signals: Signal[]
  withProfile: boolean
  memory: FamilyMemory
}) {
  const r = props.risk
  const contact = props.memory.contacts.find((c) => c.id === r?.claimed_contact)
  const odd = props.signals.find((s) => s.type === 'out_of_character')

  return (
    <section className="card caller">
      <h2>Caller</h2>
      {!r && <p className="muted">Waiting for the caller to speak.</p>}
      {r && !contact && (
        <p className="who-claim">
          {r.claimed_org ? <>Says they are from <strong>{r.claimed_org}</strong></> : 'Unknown caller'}
        </p>
      )}
      {contact && (
        <>
          <p className="who-claim">
            Says they are <strong>{contact.name}</strong> <span className="muted">({contact.relation})</span>
          </p>
          <div className="memory">
            <p className="memory-label">
              {props.withProfile ? `Compared with what Ringproof remembers about ${contact.name}` : 'Loading memory…'}
            </p>
            <ul>
              <li>Calls you <strong>“{contact.addresses_user_as}”</strong></li>
              {contact.usual_topics.length > 0 && <li>Usually talks about {contact.usual_topics.join(', ')}</li>}
              {contact.never.map((n) => <li key={n}>Never {n}</li>)}
              <li>Code word: {contact.code_word ? '••••' : 'none set'}</li>
            </ul>
            {odd && (
              <p className="mismatch">
                Unusual for {contact.name}: <q>{odd.quote}</q>
              </p>
            )}
          </div>
        </>
      )}
    </section>
  )
}
