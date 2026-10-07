// Mirrors app/models.py and the /ws/call protocol (docs/ARCHITECTURE.md §11).

export type RiskLevel = 'low' | 'medium' | 'high'
export type SignalType =
  | 'urgency'
  | 'secrecy'
  | 'transfer_ask'
  | 'impersonation'
  | 'isolation'
  | 'out_of_character'
export type ActionKind =
  | 'watch'
  | 'code_word_challenge'
  | 'is_this_you_check'
  | 'hang_up_helpline'
  | 'alert_guardian'

export type Turn = { t: number; speaker: 'caller' | 'user'; text: string }
export type Signal = { type: SignalType; quote: string }

export type RiskResult = {
  score: RiskLevel
  signals: Signal[]
  rationale: string
  claimed_contact: string | null
  claimed_org: string | null
}

export type Action = {
  kind: ActionKind
  message: string
  target: string | null
  helpline: { name: string; number: string; source: string } | null
}

export type CallEvent =
  | { type: 'started'; sample: { id: string; title: string }; duration: number }
  | { type: 'turn'; index: number; turn: Turn }
  | { type: 'risk'; upto: number; ms: number; with_profile: boolean; result: RiskResult }
  | { type: 'need_profile'; contact: string }
  | { type: 'action'; upto: number; action: Action }
  | { type: 'error'; message: string }
  | { type: 'end' }

// Family memory, kept only in this browser (see memory.ts).
export type ContactMemory = {
  id: string
  name: string
  relation: string
  addresses_user_as: string
  usual_topics: string[]
  never: string[]
  past_requests: { date: string; what: string }[]
  code_word: string | null
  email: string
}

export type FamilyMemory = {
  user: { name: string; called: string }
  contacts: ContactMemory[]
  household_rules: string[]
  alert_contact: string | null
}

export const SIGNAL_LABELS: Record<SignalType, string> = {
  urgency: 'Urgency',
  secrecy: 'Secrecy',
  transfer_ask: 'Money or OTP ask',
  impersonation: 'Impersonation',
  isolation: 'Isolation',
  out_of_character: 'Out of character',
}
