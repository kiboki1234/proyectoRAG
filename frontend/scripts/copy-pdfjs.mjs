import { cpSync, mkdirSync } from 'fs'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const here = dirname(fileURLToPath(import.meta.url))
const dest = resolve(here, '..', 'public', 'pdfjs')
mkdirSync(dest, { recursive: true })
cpSync(resolve(here, '..', 'node_modules', 'pdfjs-dist', 'web'), resolve(dest, 'web'), { recursive: true })
cpSync(resolve(here, '..', 'node_modules', 'pdfjs-dist', 'build'), resolve(dest, 'build'), { recursive: true })
console.log('✅ pdf.js copiado a public/pdfjs')
