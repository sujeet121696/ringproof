import { useCallback, useEffect, useRef, useState } from 'react'
import { profileForServer } from './memory'
import type { Action, CallEvent, FamilyMemory, RiskResult, Signal, Turn } from './types'

export type ChallengeStatus = 'waiting' | 'passed' | 'failed'
export type Challenge = { target: string; status: ChallengeStatus }

export type CallState = {
  status: 'idle' | 'live' | 'ended'
  title: string
  duration: number
  turns: Turn[]
  risk: RiskResult | null
  withProfile: boolean
  checking: boolean
  signals: Signal[] // every signal seen this call, so highlights don't flicker
  actions: Action[]
  challenge: Challenge | null
  error: string | null
}

const IDLE: CallState = {
  status: 'idle',
  title: '',
  duration: 0,
  turns: [],
  risk: null,
  withProfile: false,
  checking: false,
  signals: [],
  actions: [],
  challenge: null,
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
          }
        }
        case 'action':
          return { ...s, actions: [...s.actions, ev.action], challenge }
        case 'error':
          return { ...s, error: ev.message }
        case 'end':
          return { ...s, status: 'ended', checking: false }
        default:
          return s
      }
    })
  }

  const start = useCallback((sampleId: string, speed: number) => {
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
          sample_id: sampleId,
          speed,
          // Names and relations only; a profile follows only if the caller claims to be them.
          contacts: mem.contacts.map(({ id, name, relation }) => ({ id, name, relation })),
          household_rules: mem.household_rules,
          alert_contact: mem.alert_contact,
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
    // handle only touches refs and setState, so it is safe to leave out of the deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stop = useCallback(() => {
    ws.current?.close()
    ws.current = null
    setState((s) => ({ ...s, status: 'ended', checking: false }))
  }, [])

  useEffect(() => () => ws.current?.close(), [])

  return { state, start, stop }
}
