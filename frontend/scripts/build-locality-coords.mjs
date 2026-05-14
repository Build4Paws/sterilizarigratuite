// Build app/assets/data/locality-coords.json and app/assets/maps/county-bboxes.json
// from the GeoNames RO dataset + the existing county SVG paths in counties.ts.
//
// One-shot. Run with: node scripts/build-locality-coords.mjs
// Requires `scripts/.cache/RO.txt` (download RO.zip from GeoNames and extract).

import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')

const RO_TXT = join(__dirname, '.cache', 'RO.txt')
const JUDETE_JSON = join(ROOT, 'app', 'assets', 'data', 'judete.json')
const COUNTIES_TS = join(ROOT, 'app', 'assets', 'maps', 'counties.ts')

const OUT_LOCS = join(ROOT, 'app', 'assets', 'data', 'locality-coords.json')
const OUT_BBOXES = join(ROOT, 'app', 'assets', 'maps', 'county-bboxes.json')

// ── Constants ────────────────────────────────────────────────────────────────

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

// Feature codes we *always* keep (cities + commune capitals per GeoNames).
const KEEP_FCODES = new Set(['PPLC', 'PPLA', 'PPLA2'])
// PPL is generic populated place — GeoNames misclassifies a few real towns
// here (e.g. Adjud). We include PPL rows only when their name also appears in
// judete.json's locality list (which is already pre-filtered to cities + commune
// capitals, no satellite villages).
const PPL_FALLBACK = 'PPL'

// ── SVG path bbox parser (handles only m + implicit l + z, which is all
// the Wikimedia counties.ts uses) ─────────────────────────────────────────────

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
      const dx = parseFloat(tokens[i++])
      const dy = parseFloat(tokens[i++])
      if (firstMove || !isRel) { x = dx; y = dy } else { x += dx; y += dy }
      sx = x; sy = y
      update()
      firstMove = false
      cmd = isRel ? 'l' : 'L'
    } else if (cmd === 'l' || cmd === 'L') {
      const dx = parseFloat(tokens[i++])
      const dy = parseFloat(tokens[i++])
      if (isRel) { x += dx; y += dy } else { x = dx; y = dy }
      update()
    } else if (cmd === 'z' || cmd === 'Z') {
      x = sx; y = sy
    } else {
      i++
    }
  }
  return { x: +minX.toFixed(2), y: +minY.toFixed(2), w: +(maxX - minX).toFixed(2), h: +(maxY - minY).toFixed(2) }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function stripDiacritics(s) {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '')
}
function norm(s) {
  return stripDiacritics(String(s)).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

// ── Step 1: read existing assets ─────────────────────────────────────────────

if (!existsSync(RO_TXT)) {
  console.error(`Missing ${RO_TXT}. Download RO.zip from https://download.geonames.org/export/dump/RO.zip and extract.`)
  process.exit(1)
}

const judete = JSON.parse(readFileSync(JUDETE_JSON, 'utf8')).judete
const countiesTs = readFileSync(COUNTIES_TS, 'utf8')

// Extract { code, d } pairs from counties.ts
const countyPaths = {}
for (const m of countiesTs.matchAll(/"code":\s*"([A-Z]+)",[\s\S]*?"d":\s*"([^"]+)"/g)) {
  countyPaths[m[1]] = m[2]
}
console.log(`Loaded ${Object.keys(countyPaths).length} SVG county paths`)

// ── Step 2: compute SVG bboxes per county ────────────────────────────────────

const svgBBoxes = {}
for (const [code, d] of Object.entries(countyPaths)) {
  svgBBoxes[code] = pathBBox(d)
}

// ── Step 3: parse GeoNames, bucketed by county ───────────────────────────────

// Build a per-county set of normalized locality names from judete.json so we
// can decide which PPL rows to admit.
const judeteNamesByCounty = {}
for (const j of judete) {
  const set = new Set()
  for (const loc of j.localitati) {
    set.add(norm(loc.simplu || stripDiacritics(loc.nume)))
    set.add(norm(loc.nume))
  }
  judeteNamesByCounty[j.auto] = set
}

const ro = readFileSync(RO_TXT, 'utf8')
const lines = ro.split('\n')

// Per county: array of GeoNames candidates
const candidates = {}
let kept = 0, keptPplFallback = 0, skippedClass = 0, skippedCode = 0, skippedAdmin = 0

for (const line of lines) {
  if (!line.trim()) continue
  const cols = line.split('\t')
  // cols: 0=id 1=name 2=asciiname 3=alt 4=lat 5=lon 6=fclass 7=fcode 10=admin1 14=pop
  if (cols[6] !== 'P') { skippedClass++; continue }
  const code = ADMIN1_TO_CODE[cols[10]]
  if (!code) { skippedAdmin++; continue }
  const fcode = cols[7]
  let admit = KEEP_FCODES.has(fcode)
  const pop = parseInt(cols[14] || '0', 10)
  if (!admit && fcode === PPL_FALLBACK && pop >= 5000) {
    // Some cities/towns (e.g. Adjud) are misclassified by GeoNames as PPL.
    // Population >= 5000 catches them without admitting satellite villages.
    admit = true
    keptPplFallback++
  }
  if (!admit) { skippedCode++; continue }
  const lat = parseFloat(cols[4])
  const lon = parseFloat(cols[5])
  if (!isFinite(lat) || !isFinite(lon)) continue
  ;(candidates[code] ??= []).push({
    name: cols[1],
    ascii: cols[2],
    alt: cols[3] ? cols[3].split(',') : [],
    lat, lon,
    fcode,
    pop: parseInt(cols[14] || '0', 10),
  })
  kept++
}
console.log(`GeoNames rows kept: ${kept} (+${keptPplFallback} PPL fallback). Skipped: ${skippedClass} non-P, ${skippedCode} unmatched, ${skippedAdmin} unknown admin1`)

// ── Step 4: match against judete.json localities and project ─────────────────

const out = {}
let totalMatched = 0, totalUnmatched = 0
const unmatchedSamples = {}

for (const j of judete) {
  const code = j.auto
  const cands = candidates[code] || []
  if (!cands.length) {
    console.warn(`No GeoNames candidates for ${code} (${j.nume})`)
    continue
  }

  // Build a lookup by normalized name (covering name, ascii, alt names)
  const byName = new Map()
  for (const c of cands) {
    const keys = new Set([norm(c.name), norm(c.ascii), ...c.alt.map(norm)])
    for (const k of keys) {
      if (!k) continue
      // Prefer higher population on collisions
      const prev = byName.get(k)
      if (!prev || c.pop > prev.pop) byName.set(k, c)
    }
  }

  // Special case Bucharest: only the PPLC dot, no per-sector breakdown
  if (code === 'B') {
    const pplc = cands.find(c => c.fcode === 'PPLC')
    if (pplc) {
      const svgB = svgBBoxes[code]
      out[code] = [{
        n: 'București',
        x: +(svgB.x + svgB.w / 2).toFixed(2),
        y: +(svgB.y + svgB.h / 2).toFixed(2),
        t: 1,
        p: pplc.pop,
      }]
      totalMatched += 1
      continue
    }
  }

  // Compute geo bbox from successful matches first
  const matched = []
  const unmatched = []
  const seenGeoIds = new Set()
  for (const loc of j.localitati) {
    const name = loc.simplu || stripDiacritics(loc.nume)
    const hit = byName.get(norm(name)) ?? byName.get(norm(loc.nume))
    if (!hit) {
      unmatched.push(loc.nume)
      continue
    }
    // Dedupe: don't place the same GeoNames row twice if two judete entries collide
    const key = `${hit.lat},${hit.lon}`
    if (seenGeoIds.has(key)) continue
    seenGeoIds.add(key)
    matched.push({ src: loc.nume, hit })
  }

  if (matched.length < 2) {
    console.warn(`${code}: too few matches (${matched.length}) — skipping projection`)
    continue
  }

  // Geographic bbox from matched localities
  let gMinLat = Infinity, gMaxLat = -Infinity, gMinLon = Infinity, gMaxLon = -Infinity
  for (const { hit } of matched) {
    if (hit.lat < gMinLat) gMinLat = hit.lat
    if (hit.lat > gMaxLat) gMaxLat = hit.lat
    if (hit.lon < gMinLon) gMinLon = hit.lon
    if (hit.lon > gMaxLon) gMaxLon = hit.lon
  }
  const geoW = gMaxLon - gMinLon
  const geoH = gMaxLat - gMinLat
  const svg = svgBBoxes[code]

  if (geoW === 0 || geoH === 0) {
    console.warn(`${code}: degenerate geo bbox`)
    continue
  }

  // Inset the SVG bbox slightly so dots don't kiss the border
  const padX = svg.w * 0.06
  const padY = svg.h * 0.06
  const svgX0 = svg.x + padX
  const svgY0 = svg.y + padY
  const svgW = svg.w - padX * 2
  const svgH = svg.h - padY * 2

  const projected = matched.map(({ src, hit }) => {
    const x = svgX0 + ((hit.lon - gMinLon) / geoW) * svgW
    // SVG y grows downward, latitude grows upward → invert
    const y = svgY0 + ((gMaxLat - hit.lat) / geoH) * svgH
    // Tier: 1 = county seat / capital, 2 = town/commune
    const t = (hit.fcode === 'PPLC' || hit.fcode === 'PPLA') ? 1 : 2
    return { n: src, x: +x.toFixed(2), y: +y.toFixed(2), t, p: hit.pop }
  })

  // Sort: tier 1 first, then by population desc (biggest cities show before tiny communes)
  projected.sort((a, b) => a.t - b.t || (b.p - a.p) || a.n.localeCompare(b.n, 'ro'))

  out[code] = projected
  totalMatched += matched.length
  totalUnmatched += unmatched.length
  if (unmatched.length) unmatchedSamples[code] = unmatched.slice(0, 5)
}

console.log(`\nMatched: ${totalMatched}  Unmatched: ${totalUnmatched}  (${(totalMatched / (totalMatched + totalUnmatched) * 100).toFixed(1)}%)`)
console.log('\nUnmatched samples by county:')
for (const [code, names] of Object.entries(unmatchedSamples)) {
  console.log(`  ${code}: ${names.join(', ')}${names.length === 5 ? '…' : ''}`)
}

// ── Step 5: write outputs ────────────────────────────────────────────────────

writeFileSync(OUT_LOCS, JSON.stringify(out))
writeFileSync(OUT_BBOXES, JSON.stringify(svgBBoxes))

const sizeKB = (s) => (s.length / 1024).toFixed(1) + 'KB'
console.log(`\nWrote ${OUT_LOCS} (${sizeKB(JSON.stringify(out))})`)
console.log(`Wrote ${OUT_BBOXES} (${sizeKB(JSON.stringify(svgBBoxes))})`)
console.log(`Counties with dots: ${Object.keys(out).length} / ${judete.length}`)
console.log(`Total dots: ${Object.values(out).reduce((sum, arr) => sum + arr.length, 0)}`)
