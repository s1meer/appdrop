import { describe, it, expect } from 'vitest'

// ─── GitHub URL parsing (mirrors engine logic in TS) ─────────────────────────
function parseGitHubUrl(url: string): { valid: boolean; owner?: string; repo?: string } {
  const cleaned = url.trim().replace(/\/$/, '').replace(/\.git$/, '')
  const match = cleaned.match(/(?:https?:\/\/)?github\.com\/([^/\s?#]+)\/([^/\s?#]+)/)
  if (match) return { valid: true, owner: match[1], repo: match[2] }
  return { valid: false }
}

// ─── Status helpers ───────────────────────────────────────────────────────────
type AppStatus = 'installing' | 'ready' | 'running' | 'error' | 'stopped' | 'queued'
const STATUS_COLORS: Record<AppStatus, string> = {
  running: '#2ECC71', ready: '#4F8EF7', error: '#E74C3C',
  installing: '#F39C12', stopped: '#5A6278', queued: '#5A6278',
}
function getStatusColor(status: AppStatus): string {
  return STATUS_COLORS[status] ?? '#5A6278'
}

// ─── Install progress ─────────────────────────────────────────────────────────
interface ProgressEvent { stage: string; pct: number; label: string }
function isInstallComplete(event: ProgressEvent): boolean {
  return event.stage === 'complete' && event.pct === 100
}
function isInstallFailed(event: ProgressEvent): boolean {
  return event.stage === 'failed'
}

// ─── Port URL builder ─────────────────────────────────────────────────────────
function buildLocalUrl(port: number): string {
  return `http://localhost:${port}`
}

// ─── Tests ────────────────────────────────────────────────────────────────────
describe('GitHub URL Parser (TS)', () => {
  it('parses standard URL', () => {
    const r = parseGitHubUrl('https://github.com/comfyanonymous/ComfyUI')
    expect(r.valid).toBe(true)
    expect(r.owner).toBe('comfyanonymous')
    expect(r.repo).toBe('ComfyUI')
  })
  it('strips .git suffix', () => {
    const r = parseGitHubUrl('https://github.com/user/repo.git')
    expect(r.repo).toBe('repo')
  })
  it('strips trailing slash', () => {
    const r = parseGitHubUrl('https://github.com/user/repo/')
    expect(r.valid).toBe(true)
  })
  it('rejects non-GitHub URLs', () => {
    expect(parseGitHubUrl('https://gitlab.com/user/repo').valid).toBe(false)
    expect(parseGitHubUrl('not-a-url').valid).toBe(false)
    expect(parseGitHubUrl('').valid).toBe(false)
  })
  it('accepts URL without https', () => {
    expect(parseGitHubUrl('github.com/user/repo').valid).toBe(true)
  })
})

describe('Status Color Mapper', () => {
  it('returns green for running', () => {
    expect(getStatusColor('running')).toBe('#2ECC71')
  })
  it('returns blue for ready', () => {
    expect(getStatusColor('ready')).toBe('#4F8EF7')
  })
  it('returns red for error', () => {
    expect(getStatusColor('error')).toBe('#E74C3C')
  })
  it('returns orange for installing', () => {
    expect(getStatusColor('installing')).toBe('#F39C12')
  })
})

describe('Install Progress Events', () => {
  it('detects complete at 100%', () => {
    expect(isInstallComplete({ stage: 'complete', pct: 100, label: 'Ready' })).toBe(true)
  })
  it('not complete at partial pct', () => {
    expect(isInstallComplete({ stage: 'installing', pct: 65, label: 'Installing' })).toBe(false)
  })
  it('detects failed stage', () => {
    expect(isInstallFailed({ stage: 'failed', pct: 0, label: 'Failed' })).toBe(true)
  })
  it('not failed when running', () => {
    expect(isInstallFailed({ stage: 'cloning', pct: 15, label: 'Cloning' })).toBe(false)
  })
})

describe('Local URL Builder', () => {
  it('builds localhost URL from port', () => {
    expect(buildLocalUrl(8188)).toBe('http://localhost:8188')
    expect(buildLocalUrl(7800)).toBe('http://localhost:7800')
  })
})
