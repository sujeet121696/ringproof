// Seconds into the call as m:ss (the transcript and the call status bar use the same clock).
export const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`
