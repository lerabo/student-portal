// Запити до REST API сайту Django (DRF) від імені користувача, що увійшов.
// Сесія - у cookie sessionid, яку браузер надсилає сам; запити, що змінюють
// дані, несуть токен з cookie csrftoken у заголовку X-CSRFToken.

export class ApiError extends Error {
  constructor(status, data) {
    super(data?.detail ?? `HTTP ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function csrfToken() {
  return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1] ?? ''
}

export async function request(path, { method = 'GET', body } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken()

  const options = { headers }
  if (method !== 'GET') options.method = method
  if (body !== undefined) options.body = JSON.stringify(body)

  // fetch відхиляє Promise лише через мережу; 400 чи 403 - звичайна відповідь
  const response = await fetch(`/api/${path}`, options)
  if (response.status === 204) return null
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(response.status, data)
  return data
}
