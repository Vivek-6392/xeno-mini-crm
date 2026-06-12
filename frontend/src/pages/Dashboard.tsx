import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Campaign, CampaignsOverview, CustomerStats, getCampaigns, getCampaignsOverview, getCustomerStats } from '../lib/api'

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    draft:     'bg-gray-700 text-gray-300',
    running:   'bg-blue-900/60 text-blue-300',
    completed: 'bg-green-900/60 text-green-300',
    failed:    'bg-red-900/60 text-red-300',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls[status] ?? cls.draft}`}>
      {status}
    </span>
  )
}

const CHANNEL_COLORS: Record<string, string> = {
  whatsapp: '#25d366',
  sms:      '#3b82f6',
  email:    '#a78bfa',
  rcs:      '#f59e0b',
}

export default function Dashboard() {
  const [stats, setStats]     = useState<CustomerStats | null>(null)
  const [ovw, setOvw]         = useState<CampaignsOverview | null>(null)
  const [campaigns, setCamps] = useState<Campaign[]>([])

  useEffect(() => {
    getCustomerStats().then(setStats)
    getCampaignsOverview().then(setOvw)
    getCampaigns().then(c => setCamps(c.slice(0, 8)))
  }, [])

  // Build bar-chart data from recent campaigns
  const chartData = campaigns.map(c => ({
    name: c.name.length > 16 ? c.name.slice(0, 14) + '…' : c.name,
    Sent:      c.total_sent,
    Delivered: c.total_delivered,
    Clicked:   c.total_clicked,
    Converted: c.total_converted,
  }))

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-white">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Customers"
          value={stats?.total_customers.toLocaleString() ?? '—'}
          sub={`Avg LTV ₹${stats?.avg_lifetime_value.toLocaleString() ?? '—'}`}
        />
        <StatCard
          label="Total Revenue"
          value={stats ? `₹${stats.total_revenue.toLocaleString()}` : '—'}
          sub={`${stats?.avg_orders_per_customer.toFixed(1)} avg orders`}
        />
        <StatCard
          label="Campaigns"
          value={ovw?.total ?? '—'}
          sub={`${ovw?.running ?? 0} running · ${ovw?.completed ?? 0} completed`}
        />
        <StatCard
          label="Messages Sent"
          value={ovw?.all_time_sent.toLocaleString() ?? '—'}
          sub={`${ovw?.all_time_converted.toLocaleString() ?? 0} conversions`}
        />
      </div>

      {/* Campaign performance chart */}
      {chartData.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Campaign Performance</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="Sent"      fill="#4b5563" radius={[3,3,0,0]} />
              <Bar dataKey="Delivered" fill="#7c3aed" radius={[3,3,0,0]} />
              <Bar dataKey="Clicked"   fill="#a78bfa" radius={[3,3,0,0]} />
              <Bar dataKey="Converted" fill="#10b981" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent campaigns table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700">
        <div className="px-5 py-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-gray-300">Recent Campaigns</h2>
          <Link to="/campaigns" className="text-xs text-violet-400 hover:text-violet-300">
            View all →
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase border-b border-gray-700">
                <th className="text-left px-5 py-3">Name</th>
                <th className="text-left px-5 py-3">Channel</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-right px-5 py-3">Sent</th>
                <th className="text-right px-5 py-3">Delivered</th>
                <th className="text-right px-5 py-3">Clicked</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map(c => (
                <tr key={c.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="px-5 py-3">
                    <Link to={`/campaigns/${c.id}`} className="text-white hover:text-violet-400">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                      style={{
                        background: `${CHANNEL_COLORS[c.channel] ?? '#6b7280'}22`,
                        color: CHANNEL_COLORS[c.channel] ?? '#9ca3af',
                      }}
                    >
                      {c.channel}
                    </span>
                  </td>
                  <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-5 py-3 text-right text-gray-400">{c.total_sent}</td>
                  <td className="px-5 py-3 text-right text-gray-400">{c.total_delivered}</td>
                  <td className="px-5 py-3 text-right text-gray-400">{c.total_clicked}</td>
                </tr>
              ))}
              {campaigns.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-gray-600">
                    No campaigns yet. Chat with the AI Copilot to launch your first one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* City distribution */}
      {stats && stats.top_cities.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Customers by City</h2>
          <div className="space-y-2">
            {stats.top_cities.map(({ city, count }) => {
              const max = stats.top_cities[0].count
              const pct = Math.round((count / max) * 100)
              return (
                <div key={city} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-24 flex-shrink-0">{city}</span>
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-violet-600 h-2 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
