import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from '../api.js'
import { reply } from './fixtures.js'

describe('request', () => {
  beforeEach(() => {
    document.cookie = 'csrftoken=abc123'
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('GET - без X-CSRFToken і без тіла', async () => {
    const fetch = vi.fn(async () => reply(200, { count: 0, results: [] }))
    vi.stubGlobal('fetch', fetch)

    expect(await request('students/')).toEqual({ count: 0, results: [] })
    const [url, options] = fetch.mock.calls[0]
    expect(url).toBe('/api/students/')
    expect(options.headers).toEqual({ Accept: 'application/json' })
    expect(options.method).toBeUndefined()
    expect(options.body).toBeUndefined()
  })

  it('POST - тіло JSON і X-CSRFToken з cookie', async () => {
    const fetch = vi.fn(async () => reply(201, { id: 7 }))
    vi.stubGlobal('fetch', fetch)

    await request('grades/', { method: 'POST', body: { score: 88 } })
    const [, options] = fetch.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(options.headers['X-CSRFToken']).toBe('abc123')
    expect(options.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(options.body)).toEqual({ score: 88 })
  })

  it('204 - null', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 204 })))

    expect(await request('students/1/', { method: 'DELETE' })).toBeNull()
  })

  it('403 - ApiError зі status і data', async () => {
    const data = { detail: 'У вас недостатньо прав для виконання цієї дії.' }
    vi.stubGlobal('fetch', vi.fn(async () => reply(403, data)))

    const error = await request('students/1/', { method: 'DELETE' }).catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(403)
    expect(error.data).toEqual(data)
    expect(error.message).toBe(data.detail)
  })
})
