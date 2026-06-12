import { Bot, Rocket, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Campaign,
  Communication,
  Segment,
  createCampaign,
  getCampaign,
  getCampaignCommunications,
  getCampaigns,
  getSegments,
  launchCampaign,
} from '../lib/api'

const CHANNEL_COLORS: Record<string, string> = {
  whatsapp: '#25d366',
  sms:      '#3b82f6',
  email:    '#a78bfa',
  rcs:      '#f59e0b',
}

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    draft:     'bg-gray-700 text-gray-300',
    running:   'bg-blue-900/60 text-blue-300 animate-pulse',
    completed: 'bg-green-900/60 text-green-300',
    failed:    'bg-red-900/60 text-red-300',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls[status] ?? cls.draft}`}>
      {status}
    </span>
  )
}

function DeliveryFunnel({ campaign }: { campaign: Campaign }) {
  const data = [
    { label: 'Sent',       value: campaign.total_sent,      fill: '#4b5563' },
    { label: 'Delivered',  value: campaign.total_delivered,  fill: '#7c3aed' },
    { label: 'Open/Read',  value: campaign.total_opened + campaign.total_read, fill: '#8b5cf6' },
    { label: 'Clicked',    value: campaign.total_clicked,    fill: '#a78bfa' },
    { label: 'Converted',  value: campaign.total_converted,  fill: '#10b981' },
  ]
  const pct = (n: number) =>
    campaign.total_sent > 0 ? `${((n / campaign.total_sent) * 100).toFixed(1)}%` : '0%'

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#fff' }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-5 gap-2">
        {data.map(d => (
          <div key={d.label} className="text-center">
            <p className="text-lg font-bold text-white">{d.value}</p>
            <p className="text-xs text-gray-500">{d.label}</p>
            <p className="text-xs font-medium" style={{ color: d.fill }}>{pct(d.value)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Campaigns() {
  const navigate = useNavigate()
  const { id: paramId } = useParams<{ id?: string }>()

  const [campaigns, setCampaigns]       = useState<Campaign[]>([])
  const [selected, setSelected]         = useState<Campaign | null>(null)
  const [comms, setComms]               = useState<Communication[]>([])
  const [segments, setSegments]         = useState<Segment[]>([])
  const [showNew, setShowNew]           = useState(false)
  const [launching, setLaunching]       = useState(false)

  // New campaign form state
  const [form, setForm] = useState({
    name: '', segment_id: '', channel: 'whatsapp', message_template: 'Hi {name},',
  })

  function loadCampaigns() {
    getCampaigns().then(setCampaigns)
  }

  useEffect(() => {
    loadCampaigns()
    getSegments().then(setSegments)
  }, [])

  // Select campaign from URL param
  useEffect(() => {
    if (paramId && campaigns.length > 0) {
      const c = campaigns.find(c => c.id === paramId)
      if (c) selectCampaign(c)
    }
  }, [paramId, campaigns])

  function selectCampaign(c: Campaign) {
    setSelected(c)
    navigate(`/campaigns/${c.id}`, { replace: true })
    getCampaignCommunications(c.id).then(setComms)
  }

  // Poll running campaigns every 3s
  useEffect(() => {
    if (!selected || selected.status !== 'running') return
    const interval = setInterval(async () => {
      const refreshed = await getCampaign(selected.id)
      setSelected(refreshed)
      setCampaigns(prev => prev.map(c => c.id === refreshed.id ? refreshed : c))
    }, 3000)
    return () => clearInterval(interval)
  }, [selected?.id, selected?.status])

  async function handleLaunch(id: string) {
    setLaunching(true)
    try {
      const updated = await launchCampaign(id)
      setSelected(updated)
      setCampaigns(prev => prev.map(c => c.id === id ? updated : c))
    } catch { alert('Launch failed') }
    finally { setLaunching(false) }
  }

  async function handleCreate() {
    if (!form.name || !form.segment_id || !form.message_template) {
      alert('Fill in all fields')
      return
    }
    try {
      const c = await createCampaign(form)
      setCampaigns(prev => [c, ...prev])
      setShowNew(false)
      setForm({ name: '', segment_id: '', channel: 'whatsapp', message_template: 'Hi {name},' })
      selectCampaign(c)
    } catch { alert('Failed to create campaign') }
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Campaigns</h1>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/copilot')}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-700 hover:border-violet-600/60 text-gray-300 hover:text-white text-sm rounded-lg transition-all"
          >
            <Bot size={14} className="text-violet-400" />
            Launch with AI
          </button>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm rounded-lg transition-colors"
          >
            <Zap size={14} />
            New Campaign
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: campaign list */}
        <div className="lg:col-span-2 space-y-2">
          {campaigns.map(c => (
            <div
              key={c.id}
              onClick={() => selectCampaign(c)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                selected?.id === c.id
                  ? 'bg-violet-600/10 border-violet-600/50'
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <p className="text-sm font-medium text-white leading-tight">{c.name}</p>
                <StatusBadge status={c.status} />
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span
                  className="font-semibold uppercase"
                  style={{ color: CHANNEL_COLORS[c.channel] ?? '#6b7280' }}
                >
                  {c.channel}
                </span>
                <span>·</span>
                <span>{c.total_sent} sent</span>
                {c.total_delivered > 0 && (
                  <>
                    <span>·</span>
                    <span className="text-green-500">
                      {((c.total_delivered / c.total_sent) * 100).toFixed(0)}% delivered
                    </span>
                  </>
                )}
              </div>
            </div>
          ))}
          {campaigns.length === 0 && (
            <div className="text-center py-12 text-gray-600 text-sm">
              No campaigns yet.
            </div>
          )}
        </div>

        {/* Right: campaign detail */}
        <div className="lg:col-span-3">
          {selected ? (
            <div className="space-y-4">
              {/* Header */}
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
                <div className="flex justify-between items-start mb-1">
                  <h2 className="text-base font-semibold text-white">{selected.name}</h2>
                  <StatusBadge status={selected.status} />
                </div>
                <div className="flex gap-4 text-xs text-gray-500 mb-4">
                  <span>Channel: <span className="font-semibold" style={{ color: CHANNEL_COLORS[selected.channel] }}>{selected.channel.toUpperCase()}</span></span>
                  {selected.launched_at && (
                    <span>Launched: {new Date(selected.launched_at).toLocaleDateString('en-IN')}</span>
                  )}
                </div>

                <DeliveryFunnel campaign={selected} />

                {selected.status === 'draft' && (
                  <button
                    onClick={() => handleLaunch(selected.id)}
                    disabled={launching}
                    className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Rocket size={14} />
                    {launching ? 'Launching…' : 'Launch Campaign'}
                  </button>
                )}
              </div>

              {/* Message template */}
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Message Template</p>
                <p className="text-sm text-gray-300 whitespace-pre-wrap">{selected.message_template}</p>
              </div>

              {/* Communications table */}
              {comms.length > 0 && (
                <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                  <div className="px-5 py-3 border-b border-gray-700 text-xs text-gray-500">
                    {comms.length} individual messages
                  </div>
                  <div className="overflow-x-auto max-h-64">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-gray-800">
                        <tr className="text-gray-500 uppercase border-b border-gray-700">
                          <th className="text-left px-4 py-2">Customer ID</th>
                          <th className="text-left px-4 py-2">Status</th>
                          <th className="text-left px-4 py-2">Sent</th>
                          <th className="text-left px-4 py-2">Delivered</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comms.map(c => (
                          <tr key={c.id} className="border-b border-gray-700/40 hover:bg-gray-700/20">
                            <td className="px-4 py-2 text-gray-500 font-mono">{c.customer_id.slice(0, 8)}…</td>
                            <td className="px-4 py-2">
                              <span className={`px-1.5 py-0.5 rounded text-xs ${
                                c.status === 'delivered' || c.status === 'read' || c.status === 'opened'
                                  ? 'bg-green-900/40 text-green-400'
                                  : c.status === 'failed'
                                  ? 'bg-red-900/40 text-red-400'
                                  : c.status === 'clicked' || c.status === 'converted'
                                  ? 'bg-violet-900/40 text-violet-400'
                                  : 'bg-gray-700 text-gray-400'
                              }`}>
                                {c.status}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-gray-500">
                              {c.sent_at ? new Date(c.sent_at).toLocaleTimeString() : '—'}
                            </td>
                            <td className="px-4 py-2 text-gray-500">
                              {c.delivered_at ? new Date(c.delivered_at).toLocaleTimeString() : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 bg-gray-800 rounded-xl border border-gray-700 border-dashed">
              <p className="text-gray-600 text-sm">Select a campaign to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* New campaign modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-lg shadow-2xl">
            <div className="px-6 py-5 border-b border-gray-800">
              <h2 className="text-base font-semibold text-white">New Campaign</h2>
            </div>
            <div className="px-6 py-5 space-y-4">
              {[
                { label: 'Campaign Name', key: 'name', type: 'text', placeholder: 'e.g. June Win-Back' },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-xs text-gray-500 block mb-1">{f.label}</label>
                  <input
                    value={(form as any)[f.key]}
                    onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                    placeholder={f.placeholder}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600"
                  />
                </div>
              ))}
              <div>
                <label className="text-xs text-gray-500 block mb-1">Segment</label>
                <select
                  value={form.segment_id}
                  onChange={e => setForm(p => ({ ...p, segment_id: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600"
                >
                  <option value="">Select a segment…</option>
                  {segments.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.customer_count})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Channel</label>
                <select
                  value={form.channel}
                  onChange={e => setForm(p => ({ ...p, channel: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600"
                >
                  <option value="whatsapp">WhatsApp</option>
                  <option value="sms">SMS</option>
                  <option value="email">Email</option>
                  <option value="rcs">RCS</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Message Template (use {'{name}'} for personalisation)</label>
                <textarea
                  rows={4}
                  value={form.message_template}
                  onChange={e => setForm(p => ({ ...p, message_template: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600 resize-none"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-800 flex gap-3 justify-end">
              <button
                onClick={() => setShowNew(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 text-sm bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
              >
                Create Campaign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
