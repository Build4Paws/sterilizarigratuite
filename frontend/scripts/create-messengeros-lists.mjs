#!/usr/bin/env node
/**
 * Bulk-create one messengeros distribution list per Romanian LOCALITY
 * (~13.7k total, across 42 counties).
 *
 * Usage:
 *   # auto-login (recommended for a full run — survives token expiry):
 *   MESSENGEROS_EMAIL='you@example.com' MESSENGEROS_PASSWORD='…' \
 *     node scripts/create-messengeros-lists.mjs
 *
 *   # or supply a short-lived dashboard Bearer JWT yourself:
 *   MESSENGEROS_TOKEN='<dashboard bearer jwt>' \
 *     node scripts/create-messengeros-lists.mjs
 *
 *   node scripts/create-messengeros-lists.mjs --dry-run        # preview, no auth needed
 *   node scripts/create-messengeros-lists.mjs --only AB        # one county only
 *   node scripts/create-messengeros-lists.mjs --limit 20       # cap creations (smoke test)
 *   node scripts/create-messengeros-lists.mjs --delay 400      # ms between calls
 *   node scripts/create-messengeros-lists.mjs --project 739
 *
 * SECURITY: credentials/token are read ONLY from env vars — never hardcode them
 * in this file or commit them. The token is never logged. No PII is written.
 *
 * Why auto-login: the dashboard JWT lives ~1h, but ~13.7k polite calls take
 * ~1h too. With MESSENGEROS_EMAIL/PASSWORD set, the script re-logs-in
 * proactively before expiry (and on any 401) so the run doesn't die mid-way.
 *
 * Resumable + idempotent: progress is written to the gitignored cache file
 * incrementally; re-running skips localities already created (by name). A
 * best-effort paginated fetch of existing lists adds remote dedupe on top.
 */

import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '..')
const JUDETE_FILE = join(ROOT, 'app/assets/data/judete.json')
const OUT_DIR = join(HERE, '.cache')
const OUT_FILE = join(OUT_DIR, 'messengeros-locality-lists.json')

const API = 'https://app.messengeros.com/backend/distribution-lists'
const LOGIN = 'https://app.messengeros.com/backend/auth/login'

const args = process.argv.slice(2)
const DRY = args.includes('--dry-run')
const numArg = (flag, dflt) => {
  const i = args.indexOf(flag)
  return i >= 0 ? Number(args[i + 1]) : dflt
}
const PROJECT_ID = numArg('--project', Number(process.env.MESSENGEROS_PROJECT_ID || 739))
const DELAY = numArg('--delay', 250) // ms between create calls — be polite, don't DDOS
const LIMIT = numArg('--limit', Infinity) // cap number of *creations* this run
const onlyIdx = args.indexOf('--only')
const ONLY = onlyIdx >= 0 ? String(args[onlyIdx + 1] || '').toUpperCase() : null

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// ── auth ──────────────────────────────────────────────────────────────────
// Token lives in a mutable module var so re-login can rotate it mid-run.
let token = process.env.MESSENGEROS_TOKEN || ''
const EMAIL = process.env.MESSENGEROS_EMAIL || ''
const PASSWORD = process.env.MESSENGEROS_PASSWORD || ''
const canLogin = Boolean(EMAIL && PASSWORD)

if (!DRY && !token && !canLogin) {
  console.error('✖ Provide auth: set MESSENGEROS_EMAIL + MESSENGEROS_PASSWORD (auto-login) or MESSENGEROS_TOKEN (or use --dry-run).')
  process.exit(1)
}

const authHeaders = () => ({
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
  Accept: 'application/json',
})

/** Decode JWT `exp` (ms epoch) without verifying; 0 if unreadable. */
function tokenExpiryMs(t) {
  try {
    const payload = JSON.parse(Buffer.from(t.split('.')[1], 'base64url').toString('utf8'))
    return payload.exp ? payload.exp * 1000 : 0
  } catch {
    return 0
  }
}

async function login() {
  if (!canLogin) throw new Error('Token missing/expired and no MESSENGEROS_EMAIL/PASSWORD to re-login.')
  const res = await fetch(LOGIN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD, rememberMe: true, trustedDeviceToken: '' }),
  })
  if (!res.ok) throw new Error(`Login failed: HTTP ${res.status}`)
  const data = await res.json()
  if (!data || !data.token) throw new Error('Login response had no token.')
  token = data.token
  console.log('🔑 Authenticated (token rotated).')
}

/** Re-login if no token, or it expires within 5 min and we have creds. */
async function ensureToken() {
  if (DRY) return
  const now = Date.now()
  const exp = token ? tokenExpiryMs(token) : 0
  const expiringSoon = exp > 0 && exp - now < 5 * 60 * 1000
  if (!token || (expiringSoon && canLogin)) await login()
  else if (!token) await login()
}

// ── data → unique list names ────────────────────────────────────────────────
/**
 * Build one globally-unique list name per locality. Locality names repeat
 * (504 in-county collisions; many more cross-county), so we qualify with the
 * county code, then the `comuna`, then a numeric suffix as a last resort.
 */
function buildEntries(judete) {
  const used = new Set()
  const entries = []
  for (const j of judete) {
    for (const l of j.localitati) {
      let base = `${l.nume} (${j.auto})`
      if (used.has(base) && l.comuna) base = `${l.nume}, com. ${l.comuna} (${j.auto})`
      let name = base
      let n = 2
      while (used.has(name)) name = `${base} #${n++}`
      used.add(name)
      entries.push({ county: j.auto, countyName: j.nume, locality: l.nume, comuna: l.comuna || null, name })
    }
  }
  return entries
}

// ── remote dedupe (best-effort, paginated) ───────────────────────────────────
async function fetchExistingNames() {
  const names = new Set()
  try {
    // Try common pagination shapes; stop when a page returns nothing new.
    for (let page = 1; page <= 1000; page++) {
      const url = `${API}?projectId=${PROJECT_ID}&page=${page}&itemsPerPage=1000`
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) {
        if (page === 1) console.warn(`! Couldn't list existing (HTTP ${res.status}); relying on local cache for dedupe.`)
        break
      }
      const data = await res.json()
      const arr = Array.isArray(data) ? data : (data.items || data.data || data['hydra:member'] || [])
      if (!arr.length) break
      let added = 0
      for (const it of arr) if (it && it.name && !names.has(it.name)) { names.add(it.name); added++ }
      if (added === 0) break // no new names → server ignores paging or we've seen all
    }
  } catch (e) {
    console.warn('! Existing-list fetch failed; relying on local cache:', e.message)
  }
  return names
}

async function createList(name) {
  const doPost = () => fetch(API, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ name, description: null, projectId: PROJECT_ID }),
  })
  let res = await doPost()
  if (res.status === 401 && canLogin) {
    await login()
    res = await doPost()
  }
  const text = await res.text()
  let body
  try { body = JSON.parse(text) } catch { body = text }
  if (res.status === 401) throw new Error('401 Unauthorized — token expired/invalid and re-login unavailable')
  if (res.status === 429) throw new Error('429 Too Many Requests — back off / raise --delay')
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${typeof body === 'string' ? body : JSON.stringify(body)}`)
  const id = body && typeof body === 'object'
    ? (body.id ?? body.distributionListId ?? body.data?.id ?? null)
    : null
  return id
}

// ── persistence ───────────────────────────────────────────────────────────
async function loadProgress() {
  try {
    return JSON.parse(await readFile(OUT_FILE, 'utf8'))
  } catch {
    return {}
  }
}
async function saveProgress(out) {
  await mkdir(OUT_DIR, { recursive: true })
  await writeFile(OUT_FILE, JSON.stringify(out, null, 2))
}

async function main() {
  let judete = JSON.parse(await readFile(JUDETE_FILE, 'utf8')).judete
  if (ONLY) {
    judete = judete.filter((j) => j.auto === ONLY)
    if (!judete.length) { console.error(`✖ Unknown county code: ${ONLY}`); process.exit(1) }
  }

  const entries = buildEntries(judete)
  console.log(`${entries.length} localities${ONLY ? ` (only ${ONLY})` : ''} · project ${PROJECT_ID} · delay ${DELAY}ms · ${DRY ? 'DRY RUN' : 'LIVE'}`)
  if (!DRY && DELAY > 0) {
    const mins = ((entries.length * DELAY) / 1000 / 60).toFixed(1)
    console.log(`≈ ${mins} min at this delay (token auto-refreshes${canLogin ? '' : ' — NOT available, set EMAIL/PASSWORD'}).`)
  }

  // Resume: prior run's results (keyed by unique name).
  const out = await loadProgress()
  const doneNames = new Set(
    Object.values(out).filter((e) => e && (e.status === 'created' || e.status === 'existed')).map((e) => e.name),
  )

  await ensureToken()
  const remoteNames = DRY ? new Set() : await fetchExistingNames()
  if (remoteNames.size) console.log(`Found ${remoteNames.size} existing list(s) remotely for dedupe.`)

  // Flush progress on Ctrl-C so a long run can be resumed.
  let interrupted = false
  process.on('SIGINT', () => { interrupted = true; console.log('\n⏸  SIGINT — flushing progress…') })

  let created = 0, skipped = 0, failed = 0, processed = 0
  for (const e of entries) {
    if (interrupted) break
    processed++

    if (doneNames.has(e.name) || remoteNames.has(e.name)) {
      out[e.name] = { ...e, id: out[e.name]?.id ?? null, status: out[e.name]?.status === 'created' ? 'created' : 'existed' }
      skipped++
      continue
    }
    if (created >= LIMIT) { console.log(`Reached --limit ${LIMIT}; stopping.`); break }
    if (DRY) { console.log(`+ would create: ${e.name}`); continue }

    await ensureToken()
    try {
      const id = await createList(e.name)
      out[e.name] = { ...e, id, status: 'created' }
      created++
      if (created % 100 === 0) {
        await saveProgress(out)
        console.log(`  …${created} created (${processed}/${entries.length} scanned)`)
      }
    } catch (err) {
      failed++
      out[e.name] = { ...e, id: null, status: 'failed', error: err.message }
      console.error(`✖ ${e.name}: ${err.message}`)
      if (err.message.startsWith('401') || err.message.startsWith('429')) {
        console.error('Aborting (auth/rate-limit). Re-run to resume.')
        await saveProgress(out)
        break
      }
    }
    if (DELAY > 0) await sleep(DELAY)
  }

  if (!DRY) {
    await saveProgress(out)
    console.log(`\nMap → ${OUT_FILE}`)
  }
  console.log(`\nDone. created=${created} skipped=${skipped} failed=${failed} (of ${entries.length})`)
}

main().catch((e) => { console.error(e); process.exit(1) })
