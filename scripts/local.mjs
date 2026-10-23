// One command to check, clean, build and run Ringproof locally, as it runs in production
// (FastAPI serving the built dashboard on one port).
//
//   npm run local              everything, then serve on http://localhost:8300
//   npm run local -- --mock    same, with PROVIDER=mock (keyword rules, no model credits)
//   npm run check              everything except serving (for before a commit)
//   npm run local:tunnel       everything, then serve the public demo: port 8200 behind the
//                              Cloudflare Tunnel, links in emails to https://ringproof.kharidwise.com
//
// Port 8300 stays clear of dev (8100 + 5180) and the tunnel's server (8200). PORT=... changes it.
// The tunnel (cloudflared) serves other sites too, so it is started only if it isn't running, and
// left running when Ringproof stops. TUNNEL_CONFIG=... picks another config file.
// Any failing step stops the run, so the app only starts when every check has passed.

import { spawn, spawnSync } from 'node:child_process'
import { existsSync, rmSync } from 'node:fs'
import { createServer } from 'node:net'
import { homedir } from 'node:os'
import { join } from 'node:path'

const root = join(import.meta.dirname, '..')
const web = join(root, 'web')
const win = process.platform === 'win32'
const python = join(root, '.venv', win ? 'Scripts/python.exe' : 'bin/python')
const args = process.argv.slice(2)
const checkOnly = args.includes('--check-only')
const mock = args.includes('--mock')
const tunnel = args.includes('--tunnel')
const port = process.env.PORT ?? (tunnel ? '8200' : '8300')
const publicUrl = 'https://ringproof.kharidwise.com'
const tunnelConfig = process.env.TUNNEL_CONFIG ?? join(homedir(), '.cloudflared', 'claimtoglow.yml')

function step(title) {
  console.log(`\n\x1b[1m▶ ${title}\x1b[0m`)
}

function run(cmd, cmdArgs, opts = {}) {
  // npm is npm.cmd on Windows, which needs a shell; Python runs directly.
  const res = spawnSync(cmd, cmdArgs, { cwd: root, stdio: 'inherit', shell: win && cmd === 'npm', ...opts })
  if (res.status !== 0) {
    console.error(`\n\x1b[31m✗ Failed: ${cmd} ${cmdArgs.join(' ')}\x1b[0m`)
    process.exit(res.status ?? 1)
  }
}

function tunnelRunning() {
  const res = win
    ? spawnSync('tasklist', ['/FI', 'IMAGENAME eq cloudflared.exe', '/NH'], { encoding: 'utf8' })
    : spawnSync('pgrep', ['-x', 'cloudflared'], { encoding: 'utf8' })
  return (res.stdout ?? '').includes('cloudflared')
}

function hasModule(name) {
  return spawnSync(python, ['-c', `import ${name}`], { cwd: root }).status === 0
}

// A server left over from an earlier run would keep answering on the port with an old build.
async function portFree(p) {
  return new Promise((done) => {
    const probe = createServer().once('error', () => done(false))
    probe.listen(Number(p), '127.0.0.1', () => probe.close(() => done(true)))
  })
}

function portOwner(p) {
  if (!win) return spawnSync('lsof', ['-nP', `-iTCP:${p}`, '-sTCP:LISTEN'], { encoding: 'utf8' }).stdout?.trim() ?? ''
  const pid = spawnSync('netstat', ['-ano', '-p', 'TCP'], { encoding: 'utf8' }).stdout
    ?.split('\n').find((l) => l.includes(`:${p} `) && l.includes('LISTENING'))?.trim().split(/\s+/).pop()
  return pid ? `PID ${pid} (stop it with: taskkill /PID ${pid} /T /F)` : ''
}

step('Setup')
if (!checkOnly && !(await portFree(port))) {
  console.error(`Port ${port} is already in use, probably by an earlier Ringproof run. ${portOwner(port)}`)
  process.exit(1)
}
if (!existsSync(python)) {
  console.error('No Python environment. Run: python -m venv .venv, then install requirements (README "Setup").')
  process.exit(1)
}
if (!existsSync(join(web, 'node_modules'))) run('npm', ['ci'], { cwd: web })
if (!existsSync(join(root, '.env'))) {
  console.warn('No .env: copy .env.example to .env. Without keys, use --mock.')
}
console.log('ok')

step('Clean')
for (const dir of [join(web, 'dist'), join(root, '.pytest_cache')]) rmSync(dir, { recursive: true, force: true })
console.log('removed web/dist and .pytest_cache')

step('Lint + type check + build dashboard')
run('npm', ['run', 'lint'], { cwd: web })
run('npm', ['run', 'build'], { cwd: web })

// After the build, so the tests also cover serving the built dashboard.
step('Backend tests')
run(python, ['-m', 'pytest', 'tests', '-q', '-p', 'no:cacheprovider'])

step('Security audit (known vulnerabilities in dependencies)')
if (hasModule('pip_audit')) run(python, ['-m', 'pip_audit', '-r', 'requirements.lock', '--progress-spinner', 'off'])
else console.warn('pip-audit is not installed; skipped (pip install -r requirements.txt -c requirements.lock)')
run('npm', ['audit', '--omit=dev'], { cwd: web })

if (checkOnly) {
  console.log('\n\x1b[32m✓ All checks passed.\x1b[0m')
  process.exit(0)
}

if (tunnel) {
  step('Cloudflare Tunnel')
  if (tunnelRunning()) console.log('already running')
  else if (!existsSync(tunnelConfig)) console.warn(`No tunnel config at ${tunnelConfig}; serving locally only.`)
  else {
    // Detached, so it keeps serving the other sites on this tunnel after Ringproof stops.
    spawn('cloudflared', ['--config', tunnelConfig, 'tunnel', 'run'], { detached: true, stdio: 'ignore' }).unref()
    console.log(`started with ${tunnelConfig}`)
  }
}

const where = tunnel ? `${publicUrl} (via http://localhost:${port})` : `http://localhost:${port}`
step(`Run on ${where}${mock ? ' (PROVIDER=mock)' : ''}   Ctrl+C to stop`)
// The server watches a pipe from this script and exits when it closes, which the OS does however
// this script ends (Ctrl+C, a closed window, a killed process). Without it, a killed run on Windows
// leaves the server answering on the port with an old build.
const serve = [
  'import os, sys, threading, uvicorn',
  'threading.Thread(target=lambda: (sys.stdin.read(), os._exit(0)), daemon=True).start()',
  `sys.argv = ['uvicorn', 'app.main:app', '--port', ${JSON.stringify(String(port))}]`,
  'uvicorn.main()',
].join('\n')
const server = spawn(python, ['-c', serve], {
  cwd: root,
  stdio: ['pipe', 'inherit', 'inherit'],
  env: {
    ...process.env,
    ...(mock ? { PROVIDER: 'mock' } : {}),
    // Links in emails and the /ws/call origin check must match the public address.
    ...(tunnel ? { PUBLIC_BASE_URL: publicUrl } : {}),
  },
})
// A normal exit also stops it directly; the port check above is the last line of defence.
function stopServer() {
  if (server.exitCode !== null || !server.pid) return
  if (win) spawnSync('taskkill', ['/PID', String(server.pid), '/T', '/F'], { stdio: 'ignore' })
  else server.kill('SIGTERM')
}
process.on('exit', stopServer)
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP', 'SIGBREAK']) process.on(sig, () => process.exit(130))
server.on('exit', (code) => process.exit(code ?? 0))
