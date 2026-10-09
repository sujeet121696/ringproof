import type { ReactNode } from 'react'

// Small line icons drawn for Ringproof (24×24, stroke follows the text colour).

type Props = { size?: number }

function Icon(props: Props & { children: ReactNode }) {
  const s = props.size ?? 18
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {props.children}
    </svg>
  )
}

export const GearIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M19.5 9.7L21.9 10.4L21.9 13.6L19.5 14.3L18.9 15.7L20.1 17.9L17.9 20.1L15.7 18.9L14.3 19.5L13.6 21.9L10.4 21.9L9.7 19.5L8.3 18.9L6.1 20.1L3.9 17.9L5.1 15.7L4.5 14.3L2.1 13.6L2.1 10.4L4.5 9.7L5.1 8.3L3.9 6.1L6.1 3.9L8.3 5.1L9.7 4.5L10.4 2.1L13.6 2.1L14.3 4.5L15.7 5.1L17.9 3.9L20.1 6.1L18.9 8.3Z" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
)

export const AutoIcon = (p: Props) => (
  <Icon {...p}>
    <rect x="3" y="4" width="18" height="12" rx="2" />
    <path d="M8 20h8M12 16v4" />
  </Icon>
)

export const SunIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </Icon>
)

export const MoonIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z" />
  </Icon>
)

export const InstallIcon = (p: Props) => (
  <Icon {...p}>
    <rect x="6" y="2.5" width="12" height="19" rx="2.5" />
    <path d="M12 7v7M9 11l3 3 3-3M10.5 18.5h3" />
  </Icon>
)

export const AlertIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M10.3 3.8 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0Z" />
    <path d="M12 9.5v4.5M12 17.2v.1" />
  </Icon>
)

export const CheckIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8 12.5 2.7 2.7L16.5 9.5" />
  </Icon>
)

export const ListenIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" />
  </Icon>
)

export const FamilyIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M3 19.5a6 6 0 0 1 12 0" />
    <circle cx="17" cy="9.5" r="2.4" />
    <path d="M15.8 14.2a4.6 4.6 0 0 1 5.2 4.6" />
  </Icon>
)

export const ShieldIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 2.8 4.5 5.6v5.6c0 4.6 3.1 8.4 7.5 9.9 4.4-1.5 7.5-5.3 7.5-9.9V5.6Z" />
    <path d="m8.8 12 2.3 2.3 4.3-4.6" />
  </Icon>
)
