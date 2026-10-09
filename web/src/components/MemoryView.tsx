import { useState } from 'react'
import { eraseAll, newContactId, resetToDemo } from '../memory'
import type { ContactMemory, FamilyMemory } from '../types'

const lines = (s: string) => s.split('\n').map((l) => l.trim()).filter(Boolean)

// Past requests are edited as "2026-03: what happened", one per line.
const requestsToText = (c: ContactMemory) => c.past_requests.map((r) => `${r.date}: ${r.what}`).join('\n')
function textToRequests(s: string) {
  return lines(s).map((l) => {
    const i = l.indexOf(': ')
    return i > 0 ? { date: l.slice(0, i), what: l.slice(i + 2) } : { date: '', what: l }
  })
}

const BLANK: ContactMemory = {
  id: '', name: '', relation: '', addresses_user_as: '', usual_topics: [], never: [],
  past_requests: [], code_word: null, email: '',
}

// The family memory: everything Ringproof knows, editable and erasable by the user.
// Lives only in this browser; see memory.ts for what the server is allowed to see.
export function MemoryView(props: { memory: FamilyMemory; onChange: (m: FamilyMemory) => void }) {
  const m = props.memory
  const [editing, setEditing] = useState<ContactMemory | null>(null)
  const [confirm, setConfirm] = useState<string | null>(null) // contact id, or 'all'
  const [rule, setRule] = useState('')

  const set = (patch: Partial<FamilyMemory>) => props.onChange({ ...m, ...patch })

  function saveContact(c: ContactMemory) {
    const exists = m.contacts.some((x) => x.id === c.id)
    const contacts = exists
      ? m.contacts.map((x) => (x.id === c.id ? c : x))
      : [...m.contacts, { ...c, id: newContactId(c.name, m.contacts.map((x) => x.id)) }]
    set({ contacts })
    setEditing(null)
  }

  function deleteContact(id: string) {
    set({
      contacts: m.contacts.filter((c) => c.id !== id),
      alert_contact: m.alert_contact === id ? null : m.alert_contact,
    })
    setConfirm(null)
  }

  return (
    <div className="memory-view">
      <section className="card privacy">
        <h2>Family memory</h2>
        <p>
          Stored <strong>only in this browser</strong>. During a call, Ringproof shares just the profile of the
          person the caller claims to be, and only whether they have a code word. <strong>The code word never
          leaves this device.</strong>
        </p>
      </section>

      <section className="card">
        <h2>About you</h2>
        <div className="field-row">
          <label>Your name<input value={m.user.name} onChange={(e) => set({ user: { ...m.user, name: e.target.value } })} /></label>
          <label>Family calls you<input value={m.user.called} onChange={(e) => set({ user: { ...m.user, called: e.target.value } })} /></label>
        </div>
      </section>

      <section className="card">
        <div className="card-head">
          <h2>People who call you ({m.contacts.length})</h2>
          {!editing && <button className="btn" onClick={() => setEditing({ ...BLANK })}>+ Add person</button>}
        </div>
        {editing && <ContactForm key={editing.id || 'new'} initial={editing} onSave={saveContact} onCancel={() => setEditing(null)} />}
        {m.contacts.length === 0 && !editing && <p className="muted">No one yet. Add the people who usually call you.</p>}
        <ul className="contact-cards">
          {m.contacts.map((c) => (
            <li key={c.id} className="contact-card">
              <div className="contact-head">
                <span className="avatar" aria-hidden="true">{Array.from(c.name.trim())[0]?.toUpperCase() ?? '?'}</span>
                <div><strong>{c.name}</strong><span className="muted">{c.relation}</span></div>
              </div>
              <ul className="facts">
                <li>Calls you <strong>“{c.addresses_user_as}”</strong></li>
                {c.usual_topics.length > 0 && <li>Talks about {c.usual_topics.join(', ')}</li>}
                {c.never.map((n) => <li key={n}>Never {n}</li>)}
                {c.past_requests.map((r) => <li key={r.date + r.what}>{r.date && `${r.date}: `}{r.what}</li>)}
                <li>Code word: {c.code_word ? '•••• set' : 'none'}</li>
                {c.email && <li>Email: {c.email}</li>}
              </ul>
              {confirm === c.id ? (
                <div className="row-btns">
                  <span>Delete {c.name}?</span>
                  <button className="btn danger" onClick={() => deleteContact(c.id)}>Delete</button>
                  <button className="btn" onClick={() => setConfirm(null)}>Cancel</button>
                </div>
              ) : (
                <div className="row-btns">
                  <button className="btn" onClick={() => setEditing(c)} disabled={!!editing}>Edit</button>
                  <button className="btn" onClick={() => setConfirm(c.id)} disabled={!!editing}>Delete</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      <div className="memory-grid">
        <section className="card">
          <h2>Household rules</h2>
          <p className="muted small">Rules every caller is checked against.</p>
          <ul className="rules">
            {m.household_rules.map((r, i) => (
              <li key={r + i}>
                <span>{r}</span>
                <button className="btn small" aria-label={`Remove rule: ${r}`}
                  onClick={() => set({ household_rules: m.household_rules.filter((_, j) => j !== i) })}>Remove</button>
              </li>
            ))}
          </ul>
          <form className="add-rule" onSubmit={(e) => {
            e.preventDefault()
            if (rule.trim()) set({ household_rules: [...m.household_rules, rule.trim()] })
            setRule('')
          }}>
            <input value={rule} onChange={(e) => setRule(e.target.value)} placeholder="e.g. We never share OTPs on a call" />
            <button className="btn" type="submit">Add</button>
          </form>
        </section>

        <section className="card">
          <h2>Who to alert</h2>
          <p className="muted small">Told when a call looks like a scam.</p>
          <select value={m.alert_contact ?? ''} onChange={(e) => set({ alert_contact: e.target.value || null })}>
            <option value="">No one</option>
            {m.contacts.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.relation})</option>)}
          </select>
        </section>
      </div>

      <section className="card danger-zone">
        <h2>Your data</h2>
        {confirm === 'all' ? (
          <div className="row-btns">
            <span><strong>Erase all family memory from this browser?</strong> This cannot be undone.</span>
            <button className="btn danger" onClick={() => { eraseAll().then(props.onChange); setConfirm(null) }}>Erase everything</button>
            <button className="btn" onClick={() => setConfirm(null)}>Cancel</button>
          </div>
        ) : (
          <div className="row-btns">
            <button className="btn danger" onClick={() => setConfirm('all')}>Delete all memory</button>
            <button className="btn" onClick={() => resetToDemo().then(props.onChange)}>Load demo family</button>
          </div>
        )}
      </section>
    </div>
  )
}

function ContactForm(props: { initial: ContactMemory; onSave: (c: ContactMemory) => void; onCancel: () => void }) {
  const c = props.initial
  const [f, setF] = useState({
    name: c.name, relation: c.relation, addresses_user_as: c.addresses_user_as, email: c.email,
    topics: c.usual_topics.join('\n'), never: c.never.join('\n'), requests: requestsToText(c), code: c.code_word ?? '',
  })
  const [show, setShow] = useState(false)
  const field = (k: keyof typeof f) => ({ value: f[k], onChange: (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value }) })

  return (
    <form className="contact-form" onSubmit={(e) => {
      e.preventDefault()
      props.onSave({
        ...c,
        name: f.name.trim(), relation: f.relation.trim(), addresses_user_as: f.addresses_user_as.trim(), email: f.email.trim(),
        usual_topics: lines(f.topics), never: lines(f.never), past_requests: textToRequests(f.requests),
        code_word: f.code.trim() || null,
      })
    }}>
      <h3>{c.id ? `Edit ${c.name}` : 'Add a person'}</h3>
      <div className="field-row">
        <label>Name<input required {...field('name')} /></label>
        <label>Relation<input required placeholder="son, daughter-in-law…" {...field('relation')} /></label>
        <label>Calls you<input required placeholder="Maa, Mummy ji…" {...field('addresses_user_as')} /></label>
        <label>Email (for alerts)<input type="email" {...field('email')} /></label>
      </div>
      <div className="field-row">
        <label>Usually talks about<span className="hint">one per line</span><textarea rows={4} {...field('topics')} /></label>
        <label>Would never<span className="hint">one per line</span><textarea rows={4} {...field('never')} /></label>
        <label>Past requests<span className="hint">“2026-03: what”, one per line</span><textarea rows={4} {...field('requests')} /></label>
      </div>
      <label className="code">
        Family code word<span className="hint">never leaves this browser</span>
        <span className="code-input">
          <input type={show ? 'text' : 'password'} autoComplete="off" {...field('code')} />
          <button type="button" className="btn small" onClick={() => setShow(!show)}>{show ? 'Hide' : 'Show'}</button>
        </span>
      </label>
      <div className="row-btns">
        <button className="btn go" type="submit">Save</button>
        <button className="btn" type="button" onClick={props.onCancel}>Cancel</button>
      </div>
    </form>
  )
}
