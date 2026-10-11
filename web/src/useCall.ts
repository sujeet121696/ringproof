import { useCallback, useEffect, useRef, useState } from 'react'
import { profileForServer } from './memory'
import type { Action, ActionKind, CallEvent, FamilyMemory, Lookup, Notified, RiskResult, Signal, Turn } from './types'

export type ChallengeStatus = 'waiting' | 'passed' | 'failed'
export type Challenge = { target: string; status: ChallengeStatus }

// What to play: a sample, an uploaded recording's transcript, or the next call to the phone line.
export type CallSource = { sample_id: string } | { turns: Turn[]; title: string } | { phone: true }

export type CallState = {
  status: 'idle' | 'waiting' | 'live' | 'ended'
  number: string // the phone number to call, while waiting
  title: string
  duration: number
  turns: Turn[]
  risk: RiskResult | null
  withProfile: boolean
  checking: boolean
  signals: Signal[] // every signal seen this call, so highlights don't flicker
  actions: Action[]
  challenge: Challenge | null
  lookup: Lookup | null // latest official check (the claimed organisation can change mid-call)
  notified: Partial<Record<ActionKind, Notified>>
  checkAnswer: 'yes' | 'no' | null // the real contact's reply to "Is this you?"
  error: string | null
}

const IDLE: CallState = {
  status: 'idle',
  number: '',
  title: '',
  duration: 0,
  turns: [],
  risk: null,
  withProfile: false,
  checking: false,
  signals: [],
  actions: [],
  challenge: null,
  lookup: null,
  notified: {},
  checkAnswer: null,
  error: null,
}

// After the user asks for the code word, the caller fails after this many replies without it.
const REPLIES_BEFORE_FAIL = 2

const normalise = (s: string) =>
  s.toLowerCase().replace(/[^a-z0-9ऀ-ॿ]+/g, ' ').trim()

export function useCall(memory: FamilyMemory | null) {
  const [state, setState] = useState<CallState>(IDLE)
  const ws = useRef<WebSocket | null>(null)
  const memoryRef = useRef(memory)
  useEffect(() => {
    memoryRef.current = memory
  }, [memory])

  // Call bookkeeping. The code-word check runs here, in the browser: the word never leaves it.
  const live = useRef({ challenge: null as Challenge | null, asked: false, replies: 0, lastCallerUpto: 0 })

  const codeWordStep = (turn: Turn) => {
    const c = live.current
    if (c.challenge?.status !== 'waiting') return
    const word = memoryRef.current?.contacts.find((x) => x.id === c.challenge!.target)?.code_word
    if (!word) return
    const text = ` ${normalise(turn.text)} `
    if (turn.speaker === 'user') {
      if (text.includes(' word ')) c.asked = true
    } else if (text.includes(` ${normalise(word)} `)) {
      c.challenge = { ...c.challenge, status: 'passed' }
    } else if (c.asked && ++c.replies >= REPLIES_BEFORE_FAIL) {
      c.challenge = { ...c.challenge, status: 'failed' }
    }
  }

  const handle = (ev: CallEvent) => {
    const c = live.current
    if (ev.type === 'turn') {
      if (ev.turn.speaker === 'caller') c.lastCallerUpto = ev.index + 1
      codeWordStep(ev.turn)
    }
    if (ev.type === 'action' && ev.action.kind === 'code_word_challenge' && ev.action.target) {
      c.challenge = { target: ev.action.target, status: 'waiting' }
    }
    const challenge = c.challenge
    const lastCallerUpto = c.lastCallerUpto

    setState((s) => {
      switch (ev.type) {
        case 'waiting':
          return { ...IDLE, status: 'waiting', number: ev.number }
        case 'started':
          return { ...IDLE, status: 'live', title: ev.sample.title, duration: ev.duration }
        case 'turn':
          return {
            ...s,
            turns: [...s.turns, ev.turn],
            challenge,
            checking: ev.turn.speaker === 'caller' || s.checking,
          }
        case 'risk': {
          const seen = new Set(s.signals.map((x) => x.type + x.quote))
          const fresh = ev.result.signals.filter((x) => !seen.has(x.type + x.quote))
          return {
            ...s,
            risk: ev.result,
            withProfile: ev.with_profile,
            signals: [...s.signals, ...fresh],
            checking: ev.upto < lastCallerUpto,
            error: null, // a check worked again, so an earlier "check failed" is out of date
          }
        }
        case 'action':
          return { ...s, actions: [...s.actions, ev.action], challenge }
        case 'lookup':
          return { ...s, lookup: { ...ev.result, ok: ev.ok } }
        case 'notified':
          return { ...s, notified: { ...s.notified, [ev.kind]: { ok: ev.ok, reason: ev.reason } } }
        case 'check_answer':
          return { ...s, checkAnswer: ev.answer }
        case 'error':
          return { ...s, error: ev.message }
        case 'end':
          return { ...s, status: 'ended', checking: false }
        default:
          return s
      }
    })
  }

  const start = useCallback((source: CallSource, speed: number) => {
    const mem = memoryRef.current
    if (!mem) return
    ws.current?.close()
    live.current = { challenge: null, asked: false, replies: 0, lastCallerUpto: 0 }
    setState(IDLE)

    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const socket = new WebSocket(`${proto}://${location.host}/ws/call`)
    ws.current = socket
    socket.onopen = () =>
      socket.send(
        JSON.stringify({
          type: 'start',
          ...source,
          speed,
          // Names and relations only; a profile follows only if the caller claims to be them.
          contacts: mem.contacts.map(({ id, name, relation }) => ({ id, name, relation })),
          household_rules: mem.household_rules,
          alert_contact: mem.alert_contact,
          // Only the alert contact's email, so Ringproof can alert them.
          alert_email: mem.contacts.find((x) => x.id === mem.alert_contact)?.email ?? '',
          user_called: mem.user.called,
        }),
      )
    socket.onmessage = (msg) => {
      if (ws.current !== socket) return // a newer call replaced this one
      const ev: CallEvent = JSON.parse(msg.data)
      if (ev.type === 'need_profile') {
        const contact = memoryRef.current?.contacts.find((x) => x.id === ev.contact)
        if (contact) socket.send(JSON.stringify({ type: 'profile', profile: profileForServer(contact) }))
        return
      }
      handle(ev)
    }
    socket.onerror = () => {
      if (ws.current === socket) setState((s) => ({ ...s, error: 'Lost connection to Ringproof.' }))
    }
    // 1000 is the normal close after `end`. Anything else (busy, unknown sample, server gone)
    // shows the server's reason, so the screen never sits silently.
    socket.onclose = (e) => {
      if (ws.current !== socket || e.code === 1000) return
      setState((s) => ({
        ...s,
        status: s.status === 'live' ? 'ended' : s.status === 'waiting' ? 'idle' : s.status,
        checking: false,
        error: e.reason || 'Lost connection to Ringproof.',
      }))
    }
    // handle only touches refs and setState, so it is safe to leave out of the deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stop = useCallback(() => {
    ws.current?.close()
    ws.current = null
    setState((s) => (s.status === 'waiting' ? IDLE : { ...s, status: 'ended', checking: false }))
  }, [])

  useEffect(() => () => ws.current?.close(), [])

  return { state, start, stop }
}
