// Privacy and terms in plain words. Keep every line true to the code: if what is sent or kept
// changes (useCall.ts, app/session.py, app/notify.py), update this page with it.

const REPO = 'https://github.com/sujeet121696/ringproof'

export function PrivacyView() {
  return (
    <div className="memory-view legal">
      <section className="card">
        <h2>Privacy</h2>
        <p>
          Ringproof is a hackathon demo. It has no accounts, sets no cookies and runs no analytics or ads.
          The fonts are served from this site.
        </p>
      </section>

      <section className="card">
        <h2>What stays on this device</h2>
        <ul>
          <li>Your family memory (people, how they talk, household rules, code words), in this browser's storage.</li>
          <li>Your theme choice.</li>
          <li><strong>Code words never leave this device.</strong> They are checked here, in the browser.</li>
        </ul>
      </section>

      <section className="card">
        <h2>What is sent during a call, and to whom</h2>
        <ul>
          <li><strong>Ringproof's server</strong> gets the transcript, the names and relations of your contacts,
            your household rules, what the family calls you, and the alert contact's email. If the caller claims
            to be one of your contacts, it also gets that one person's profile and email (never their code word).</li>
          <li><strong>Nebius Token Factory</strong> (NVIDIA Nemotron models) gets the transcript, contacts, rules
            and that profile, to judge the risk.</li>
          <li><strong>Tavily</strong> gets only the name of an organisation the caller claims to be from, to find
            its official pages.</li>
          <li><strong>Email (Gmail)</strong> carries the alert to your trusted contact and the "Is this you?"
            check. The email has no transcript.</li>
          <li>An <strong>uploaded recording</strong> goes to Ringproof's speech service on a Nebius GPU to be
            transcribed. A <strong>phone call</strong> comes in through Vobiz.</li>
          <li>The site is served through <strong>Cloudflare</strong>.</li>
        </ul>
        <p className="muted">
          Ringproof's server keeps nothing after a call ends: no transcript, no recording, no memory. The services
          above handle data under their own terms.
        </p>
      </section>

      <section className="card">
        <h2>Delete or change your data</h2>
        <p>
          Edit or delete anyone in <em>Family memory</em>, or use <em>Delete all</em> there. Clearing this site's data
          in your browser removes everything too. For any other question, open an issue
          on <a href={REPO + '/issues'} target="_blank" rel="noreferrer">GitHub</a>.
        </p>
      </section>

      <section className="card">
        <h2>Terms</h2>
        <ul>
          <li>Ringproof is a demo, provided as is, with no guarantee. It can miss a scam or warn about a real
            call. Never rely on it alone.</li>
          <li>If you have lost money to a scam, call the National Cyber Crime Helpline <strong>1930</strong> or
            report at <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">cybercrime.gov.in</a>.</li>
          <li>The sample calls are scripted. The names in the demo family are used with consent, and all other
            details are made up.</li>
          <li>Add only people who agree to be in your memory and to get Ringproof emails. Not for use by children.</li>
          <li>Source code under the MIT License on <a href={REPO} target="_blank" rel="noreferrer">GitHub</a>.</li>
        </ul>
      </section>
    </div>
  )
}
