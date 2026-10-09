// Family memory lives only in this browser, in IndexedDB. The server never stores it.
// First run seeds it from the demo family (/api/seed/family); after that this copy is the only one.

import type { ContactMemory, FamilyMemory } from './types'

const DB = 'ringproof'
const STORE = 'memory'
const KEY = 'family'

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function run<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest): Promise<T> {
  const db = await open()
  return new Promise((resolve, reject) => {
    const req = fn(db.transaction(STORE, mode).objectStore(STORE))
    req.onsuccess = () => resolve(req.result as T)
    req.onerror = () => reject(req.error)
  })
}

const getMemory = () => run<FamilyMemory | undefined>('readonly', (s) => s.get(KEY))
export const saveMemory = (m: FamilyMemory) => run('readwrite', (s) => s.put(m, KEY))

const fetchSeed = (): Promise<FamilyMemory> => fetch('/api/seed/family').then((r) => r.json())

export async function loadOrSeed(): Promise<FamilyMemory> {
  const existing = await getMemory()
  if (existing) return existing
  const seed = await fetchSeed()
  await saveMemory(seed)
  return seed
}

// Delete-all: overwrite the one record with an empty one in a single write (so a reload mid-way can't
// bring the demo family back, and the empty record stops it being re-seeded).
export async function eraseAll(): Promise<FamilyMemory> {
  const empty: FamilyMemory = { user: { name: '', called: '' }, contacts: [], household_rules: [], alert_contact: null }
  await saveMemory(empty)
  return empty
}

export async function resetToDemo(): Promise<FamilyMemory> {
  const seed = await fetchSeed()
  await saveMemory(seed)
  return seed
}

// Stable id from the name, unique within the family (the model refers to contacts by id).
export function newContactId(name: string, taken: string[]): string {
  const base = name.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'contact'
  let id = base
  for (let n = 2; taken.includes(id); n++) id = `${base}-${n}`
  return id
}

// What the server may see about the claimed caller: no code word, only whether one exists.
export function profileForServer(c: ContactMemory) {
  return {
    id: c.id,
    name: c.name,
    relation: c.relation,
    addresses_user_as: c.addresses_user_as,
    usual_topics: c.usual_topics,
    never: c.never,
    past_requests: c.past_requests.map((r) => `${r.date}: ${r.what}`),
    has_code_word: Boolean(c.code_word),
    email: c.email, // only to send this contact the "Is this you?" check
  }
}
