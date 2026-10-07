// PNG icons from the SVGs, same set as kharidwise: apple-touch-icon, 192/512, maskable 512,
// and 16/32/48 PNGs that make_ico.py packs into favicon.ico.
import sharp from 'sharp'
import { mkdirSync, readFileSync } from 'node:fs'

const [src, out] = process.argv.slice(2)
mkdirSync(`${out}/icons`, { recursive: true })
const mark = readFileSync(`${src}/logo-mark.svg`)
const fav = readFileSync(`${src}/favicon.svg`)
const PAGE_BG = '#f6f4fb' // kharidwise light page background

const render = (svg, size) => sharp(svg, { density: 1200 }).resize(size, size).png().toBuffer()

// Mark centred on a solid square; `inner` is the share of the square the mark fills.
async function onSquare(svg, size, inner, bg, file) {
  const m = Math.round(size * inner)
  await sharp({ create: { width: size, height: size, channels: 4, background: bg } })
    .composite([{ input: await render(svg, m), gravity: 'center' }])
    .png()
    .toFile(file)
}

await onSquare(mark, 180, 0.82, '#ffffff', `${out}/apple-touch-icon.png`) // iOS: no transparency
await onSquare(mark, 192, 0.86, { r: 0, g: 0, b: 0, alpha: 0 }, `${out}/icons/icon-192.png`)
await onSquare(mark, 512, 0.86, { r: 0, g: 0, b: 0, alpha: 0 }, `${out}/icons/icon-512.png`)
// Maskable: Android may crop to a circle; keep the mark inside the central safe zone.
await onSquare(mark, 512, 0.62, PAGE_BG, `${out}/icons/icon-maskable-512.png`)
for (const s of [16, 32, 48]) await sharp(await render(fav, s)).toFile(`${out}/fav-${s}.png`)
console.log('pngs written')
