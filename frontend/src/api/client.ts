import type { Ticket, AuditLog, User, TicketMetrics } from '../types'

const TOKEN_KEY = 'quickdesk_token'

export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setStoredToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const clearStoredToken = () => {
  localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorDetail = `Request failed with HTTP ${response.status}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail)
      }
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorDetail)
  }

  return response.json() as Promise<T>
}

export const api = {
  // Authentication
  login: async (email: string, password: string) => {
    const data = await request<{ access_token: string; token_type: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setStoredToken(data.access_token)
    return data
  },

  getMe: async (): Promise<User> => {
    return request<User>('/api/auth/me')
  },

  // Tickets
  createTicket: async (payload: { title: string; description: string; attachment_filename?: string }): Promise<Ticket> => {
    return request<Ticket>('/api/tickets', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  getMyTickets: async (): Promise<Ticket[]> => {
    return request<Ticket[]>('/api/tickets/my')
  },

  getAllTickets: async (filters: { search?: string; status?: string; category?: string; priority?: string } = {}): Promise<Ticket[]> => {
    const params = new URLSearchParams()
    if (filters.search) params.append('search', filters.search)
    if (filters.status) params.append('status', filters.status)
    if (filters.category) params.append('category', filters.category)
    if (filters.priority) params.append('priority', filters.priority)

    const queryStr = params.toString() ? `?${params.toString()}` : ''
    return request<Ticket[]>(`/api/tickets${queryStr}`)
  },

  getTicketDetail: async (id: number): Promise<Ticket> => {
    return request<Ticket>(`/api/tickets/${id}`)
  },

  overrideClassification: async (id: number, payload: { category?: string; priority?: string }): Promise<Ticket> => {
    return request<Ticket>(`/api/tickets/${id}/classification`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  replyAndResolve: async (id: number, reply: string): Promise<Ticket> => {
    return request<Ticket>(`/api/tickets/${id}/reply`, {
      method: 'POST',
      body: JSON.stringify({ reply }),
    })
  },

  regenerateDraftReply: async (id: number): Promise<Ticket> => {
    return request<Ticket>(`/api/tickets/${id}/draft-reply`, {
      method: 'POST',
    })
  },

  getAuditLogs: async (id: number): Promise<AuditLog[]> => {
    return request<AuditLog[]>(`/api/tickets/${id}/audit`)
  },

  getMetrics: async (): Promise<TicketMetrics> => {
    return request<TicketMetrics>('/api/tickets/metrics')
  },
}
