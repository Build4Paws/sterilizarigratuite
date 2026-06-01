// Rebuild app/assets/data/locality-coords.json so it covers EVERY locality the
// backend knows about (GET /counties/{code}/localities), each with approximate
// SVG coordinates.
//
// Names come from the backend API (via the local Nuxt proxy, which signs the
// AWS request). Coordinates come from the GeoNames RO dataset (lat/lon),
// projected into each county's SVG bbox — same projection the old
// build-locality-coords.mjs used, but matching against the full P-class set so
// small villages resolve too.
//
// Prereqs:
//   - `scripts/.cache/RO.txt` (download RO.zip from GeoNames and extract)
//   - the Nuxt dev server running (default http://localhost:3000)
//
// Run: node scripts/build-localities-from-api.mjs
// Override proxy: PROXY_BASE=http://localhost:3001 node scripts/build-localities-from-api.mjs

import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')

const RO_TXT = join(__dirname, '.cache', 'RO.txt')
const JUDETE_JSON = join(ROOT, 'app', 'assets', 'data', 'judete.json')
const COUNTIES_TS = join(ROOT, 'app', 'assets', 'maps', 'counties.ts')
const OUT_LOCS = join(ROOT, 'app', 'assets', 'data', 'locality-coords.json')

const PROXY_BASE = process.env.PROXY_BASE || 'http://localhost:3000'

const ADMIN1_TO_CODE = {
  '01': 'AB', '02': 'AR', '03': 'AG', '04': 'BC', '05': 'BH',
  '06': 'BN', '07': 'BT', '08': 'BR', '09': 'BV', '10': 'B',
  '11': 'BZ', '12': 'CS', '13': 'CJ', '14': 'CT', '15': 'CV',
  '16': 'DB', '17': 'DJ', '18': 'GL', '19': 'GJ', '20': 'HR',
  '21': 'HD', '22': 'IL', '23': 'IS', '25': 'MM', '26': 'MH',
  '27': 'MS', '28': 'NT', '29': 'OT', '30': 'PH', '31': 'SJ',
  '32': 'SM', '33': 'SB', '34': 'SV', '35': 'TR', '36': 'TM',
  '37': 'TL', '38': 'VS', '39': 'VL', '40': 'VN', '41': 'CL',
  '42': 'GR', '43': 'IF',
}

// county-seat / county-second-seat feature codes → tier 1 (bigger dot)
const TIER1_FCODES = new Set(['PPLC', 'PPLA', 'PPLA2'])

// ── SVG path bbox parser (m + implicit l + z) ────────────────────────────────
function pathBBox(d) {
  const tokens = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[+-]?\d+)?/g)
  let x = 0, y = 0, sx = 0, sy = 0
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  let cmd = ''
  let firstMove = true
  const update = () => {
    if (x < minX) minX = x
    if (y < minY) minY = y
    if (x > maxX) maxX = x
    if (y > maxY) maxY = y
  }
  let i = 0
  while (i < tokens.length) {
    const t = tokens[i]
    if (/[a-zA-Z]/.test(t)) { cmd = t; i++; continue }
    const isRel = cmd === cmd.toLowerCase()
    if (cmd === 'm' || cmd === 'M') {
      const dx = parseFloat(tokens[i++]); const dy = parseFloat(tokens[i++])
      if (firstMove || !isRel) { x = dx; y = dy } else { x += dx; y += dy }
      sx = x; sy = y; update(); firstMove = false; cmd = isRel ? 'l' : 'L'
    } else if (cmd === 'l' || cmd === 'L') {
      const dx = parseFloat(tokens[i++]); const dy = parseFloat(tokens[i++])
      if (isRel) { x += dx; y += dy } else { x = dx; y = dy }
      update()
    } else if (cmd === 'z' || cmd === 'Z') {
      x = sx; y = sy
    } else { i++ }
  }
  return { x: +minX.toFixed(2), y: +minY.toFixed(2), w: +(maxX - minX).toFixed(2), h: +(maxY - minY).toFixed(2) }
}

function stripDiacritics(s) { return s.normalize('NFD').replace(/[̀-ͯ]/g, '') }
function norm(s) { return stripDiacritics(String(s)).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() }

// ── Step 1: assets ───────────────────────────────────────────────────────────
if (!existsSync(RO_TXT)) {
  console.error(`Missing ${RO_TXT}. Download RO.zip from https://download.geonames.org/export/dump/RO.zip and extract.`)
  process.exit(1)
}

const judete = JSON.parse(readFileSync(JUDETE_JSON, 'utf8')).judete
const countiesTs = readFileSync(COUNTIES_TS, 'utf8')

const countyPaths = {}
for (const m of countiesTs.matchAll(/"code":\s*"([A-Z]+)",[\s\S]*?"d":\s*"([^"]+)"/g)) {
  countyPaths[m[1]] = m[2]
}
const svgBBoxes = {}
for (const [code, d] of Object.entries(countyPaths)) svgBBoxes[code] = pathBBox(d)

// ── Step 2: bucket ALL P-class GeoNames rows by county ───────────────────────
const candidates = {}
for (const line of readFileSync(RO_TXT, 'utf8').split('\n')) {
  if (!line.trim()) continue
  const cols = line.split('\t')
  // 0=id 1=name 2=ascii 3=alt 4=lat 5=lon 6=fclass 7=fcode 10=admin1 14=pop
  if (cols[6] !== 'P') continue
  const code = ADMIN1_TO_CODE[cols[10]]
  if (!code) continue
  const lat = parseFloat(cols[4]); const lon = parseFloat(cols[5])
  if (!isFinite(lat) || !isFinite(lon)) continue
  ;(candidates[code] ??= []).push({
    name: cols[1], ascii: cols[2], alt: cols[3] ? cols[3].split(',') : [],
    lat, lon, fcode: cols[7], pop: parseInt(cols[14] || '0', 10),
  })
}

// ── Step 3: fetch all localities per county from the backend (via proxy) ─────
async function fetchLocalities(code) {
  const res = await fetch(`${PROXY_BASE}/api/counties/${encodeURIComponent(code)}/localities`)
  if (!res.ok) throw new Error(`${code}: HTTP ${res.status}`)
  const json = await res.json()
  return Array.isArray(json) ? json : (json.localities ?? [])
}

const out = {}
let totalLocs = 0, totalMatched = 0, totalUnmatched = 0
const unmatchedSamples = {}

for (const j of judete) {
  const code = j.auto
  let apiLocs
  try { apiLocs = await fetchLocalities(code) }
  catch (e) { console.warn(`! ${code}: fetch failed (${e.message}) — skipping`); continue }
  totalLocs += apiLocs.length

  // Bucharest: a single dot at the county centroid (API returns sectors).
  if (code === 'B') {
    const b = svgBBoxes[code]
    out[code] = [{ n: 'București', x: +(b.x + b.w / 2).toFixed(2), y: +(b.y + b.h / 2).toFixed(2), t: 1, p: 0 }]
    totalMatched += 1
    console.log(`  B: 1 dot (centroid)`) ; continue
  }

  const cands = candidates[code] || []
  // name → best candidate (prefer higher population on collision)
  const byName = new Map()
  for (const c of cands) {
    for (const k of new Set([norm(c.name), norm(c.ascii), ...c.alt.map(norm)])) {
      if (!k) continue
      const prev = byName.get(k)
      if (!prev || c.pop > prev.pop) byName.set(k, c)
    }
  }

  const matched = []
  const unmatched = []
  const seenGeo = new Set()
  for (const loc of apiLocs) {
    const hit = byName.get(norm(loc.name))
    if (!hit) { unmatched.push(loc.name); continue }
    const key = `${hit.lat},${hit.lon}`
    if (seenGeo.has(key)) continue   // don't stack two names on one point
    seenGeo.add(key)
    matched.push({ name: loc.name, hit })
  }

  if (matched.length < 2) {
    console.warn(`! ${code}: too few matches (${matched.length}) — skipping`)
    continue
  }

  // geo bbox of matches → inset SVG bbox
  let gMinLat = Infinity, gMaxLat = -Infinity, gMinLon = Infinity, gMaxLon = -Infinity
  for (const { hit } of matched) {
    gMinLat = Math.min(gMinLat, hit.lat); gMaxLat = Math.max(gMaxLat, hit.lat)
    gMinLon = Math.min(gMinLon, hit.lon); gMaxLon = Math.max(gMaxLon, hit.lon)
  }
  const geoW = gMaxLon - gMinLon || 1e-6
  const geoH = gMaxLat - gMinLat || 1e-6
  const svg = svgBBoxes[code]
  const padX = svg.w * 0.06, padY = svg.h * 0.06
  const sx0 = svg.x + padX, sy0 = svg.y + padY, sw = svg.w - padX * 2, sh = svg.h - padY * 2

  const projected = matched.map(({ name, hit }) => ({
    n: name,
    x: +(sx0 + ((hit.lon - gMinLon) / geoW) * sw).toFixed(2),
    y: +(sy0 + ((gMaxLat - hit.lat) / geoH) * sh).toFixed(2),   // invert: lat↑ = y↓
    t: TIER1_FCODES.has(hit.fcode) ? 1 : 2,
    p: hit.pop,
  }))
  projected.sort((a, b) => a.t - b.t || (b.p - a.p) || a.n.localeCompare(b.n, 'ro'))

  out[code] = projected
  totalMatched += matched.length
  totalUnmatched += unmatched.length
  if (unmatched.length) unmatchedSamples[code] = unmatched.slice(0, 6)
  console.log(`  ${code}: ${apiLocs.length} api → ${projected.length} placed, ${unmatched.length} unmatched`)
}

// ── Step 4: write ────────────────────────────────────────────────────────────
writeFileSync(OUT_LOCS, JSON.stringify(out))
const sizeKB = (s) => (s.length / 1024).toFixed(1) + 'KB'
console.log(`\nWrote ${OUT_LOCS} (${sizeKB(JSON.stringify(out))})`)
console.log(`Counties: ${Object.keys(out).length}/${judete.length}  API localities: ${totalLocs}  placed: ${totalMatched}  unmatched: ${totalUnmatched} (${(totalMatched / totalLocs * 100).toFixed(1)}% placed)`)
console.log('\nUnmatched samples:')
for (const [code, names] of Object.entries(unmatchedSamples)) console.log(`  ${code}: ${names.join(', ')}`)
