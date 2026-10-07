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

export const getMemory = () => run<FamilyMemory | undefined>('readonly', (s) => s.get(KEY))
export const saveMemory = (m: FamilyMemory) => run('readwrite', (s) => s.put(m, KEY))
export const deleteMemory = () => run('readwrite', (s) => s.delete(KEY))

export async function loadOrSeed(): Promise<FamilyMemory> {
  const existing = await getMemory()
  if (existing) return existing
  const seed: FamilyMemory = await fetch('/api/seed/family').then((r) => r.json())
  await saveMemory(seed)
  return seed
}

// What the server may see about a contact: no code word, only whether one exists.
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
  }
}
