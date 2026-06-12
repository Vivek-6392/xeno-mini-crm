import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Customer {
  id: string
  name: string
  email: string
  phone?: string
  city?: string
  total_orders: number
  total_spent: number
  last_order_date?: string
  created_at: string
}

export interface CustomerStats {
  total_customers: number
  total_revenue: number
  avg_lifetime_value: number
  avg_orders_per_customer: number
  top_cities: Array<{ city: string; count: number }>
}

export interface Segment {
  id: string
  name: string
  description: string
  rules: Record<string, unknown>
  customer_count: number
  created_by_ai: boolean
  created_at: string
}

export interface SegmentPreview {
  matching_count: number
  sample: Array<{ id: string; name: string; city: string; total_spent: number; total_orders: number }>
}

export interface Campaign {
  id: string
  name: string
  segment_id: string
  channel: string
  message_template: string
  status: 'draft' | 'running' | 'completed' | 'failed'
  total_sent: number
  total_delivered: number
  total_failed: number
  total_opened: number
  total_read: number
  total_clicked: number
  total_converted: number
  created_at: string
  launched_at?: string
  completed_at?: string
}

export interface CampaignsOverview {
  total: number
  running: number
  completed: number
  all_time_sent: number
  all_time_delivered: number
  all_time_clicked: number
  all_time_converted: number
}

export interface Communication {
  id: string
  campaign_id: string
  customer_id: string
  channel: string
  message: string
  status: string
  queued_at: string
  sent_at?: string
  delivered_at?: string
  opened_at?: string
  read_at?: string
  clicked_at?: string
  converted_at?: string
  failed_at?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// ── Customers ─────────────────────────────────────────────────────────────────

export const getCustomers = (city?: string) =>
  api.get<Customer[]>('/api/customers/', { params: { city, limit: 200 } }).then(r => r.data)

export const getCustomerStats = () =>
  api.get<CustomerStats>('/api/customers/stats/overview').then(r => r.data)

export const createCustomer = (data: { name: string; email: string; phone?: string; city?: string }) =>
  api.post<Customer>('/api/customers/', data).then(r => r.data)

export const importCustomersCSV = async (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ created: number; skipped: number }>('/api/customers/import/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

// ── Orders ────────────────────────────────────────────────────────────────────

export const createOrder = (data: { customer_id: string; amount: number; items?: unknown[]; channel?: string }) =>
  api.post('/api/orders/', data).then(r => r.data)

// ── Segments ──────────────────────────────────────────────────────────────────

export const getSegments = () =>
  api.get<Segment[]>('/api/segments/').then(r => r.data)

export const getSegment = (id: string) =>
  api.get<Segment>(`/api/segments/${id}`).then(r => r.data)

export const previewSegment = (rules: Record<string, unknown>) =>
  api.post<SegmentPreview>('/api/segments/preview', { rules }).then(r => r.data)

export const createSegment = (data: { name: string; description: string; rules: Record<string, unknown> }) =>
  api.post<Segment>('/api/segments/', data).then(r => r.data)

export const getSegmentCustomers = (id: string) =>
  api.get<Customer[]>(`/api/segments/${id}/customers`).then(r => r.data)

export const deleteSegment = (id: string) =>
  api.delete(`/api/segments/${id}`)

// ── Campaigns ─────────────────────────────────────────────────────────────────

export const getCampaigns = () =>
  api.get<Campaign[]>('/api/campaigns/').then(r => r.data)

export const getCampaign = (id: string) =>
  api.get<Campaign>(`/api/campaigns/${id}`).then(r => r.data)

export const getCampaignsOverview = () =>
  api.get<CampaignsOverview>('/api/campaigns/stats/overview').then(r => r.data)

export const createCampaign = (data: {
  name: string
  segment_id: string
  channel: string
  message_template: string
}) => api.post<Campaign>('/api/campaigns/', data).then(r => r.data)

export const launchCampaign = (id: string) =>
  api.post<Campaign>(`/api/campaigns/${id}/launch`).then(r => r.data)

export const getCampaignCommunications = (id: string) =>
  api.get<Communication[]>(`/api/campaigns/${id}/communications`, { params: { limit: 100 } }).then(r => r.data)

// ── Agent (SSE streaming) ─────────────────────────────────────────────────────

export async function streamAgentChat(
  message: string,
  history: ChatMessage[],
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void
) {
  const resp = await fetch(`${API_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!resp.ok || !resp.body) {
    onError('Agent request failed')
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const payload = JSON.parse(line.slice(6))
        if (payload.type === 'token') onToken(payload.content)
        else if (payload.type === 'done') onDone()
        else if (payload.type === 'error') onError(payload.content)
      } catch {
        // malformed chunk — ignore
      }
    }
  }
}
