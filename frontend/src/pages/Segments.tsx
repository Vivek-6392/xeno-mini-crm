import { Bot, Plus, Trash2, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Customer,
  Segment,
  SegmentPreview,
  createSegment,
  deleteSegment,
  getSegmentCustomers,
  getSegments,
  previewSegment,
} from '../lib/api'

const FIELD_OPTIONS = [
  { value: 'total_spent',            label: 'Total Spent (₹)' },
  { value: 'total_orders',           label: 'Total Orders' },
  { value: 'days_since_last_order',  label: 'Days Since Last Order' },
  { value: 'city',                   label: 'City' },
  { value: 'created_within_days',    label: 'Customer Age (days)' },
]

const OP_MAP: Record<string, string[]> = {
  total_spent:           ['gte','lte','gt','lt','eq'],
  total_orders:          ['gte','lte','gt','lt','eq'],
  days_since_last_order: ['gte','lte'],
  city:                  ['in','not_in'],
  created_within_days:   ['lte'],
}

interface Condition {
  field: string
  operator: string
  value: string
}

function defaultOp(field: string) {
  return OP_MAP[field]?.[0] ?? 'gte'
}

export default function Segments() {
  const navigate = useNavigate()
  const [segments, setSegments]   = useState<Segment[]>([])
  const [selected, setSelected]   = useState<Segment | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])

  // Builder state
  const [showBuilder, setShowBuilder] = useState(false)
  const [name, setName]               = useState('')
  const [desc, setDesc]               = useState('')
  const [operator, setOperator]       = useState<'AND' | 'OR'>('AND')
  const [conditions, setConditions]   = useState<Condition[]>([
    { field: 'total_spent', operator: 'gte', value: '5000' },
  ])
  const [preview, setPreview]         = useState<SegmentPreview | null>(null)
  const [previewing, setPreviewing]   = useState(false)
  const [saving, setSaving]           = useState(false)

  function load() { getSegments().then(setSegments) }
  useEffect(() => { load() }, [])

  function selectSegment(seg: Segment) {
    setSelected(seg)
    getSegmentCustomers(seg.id).then(setCustomers)
  }

  function addCondition() {
    setConditions(prev => [...prev, { field: 'total_spent', operator: 'gte', value: '' }])
  }

  function updateCondition(i: number, updates: Partial<Condition>) {
    setConditions(prev => prev.map((c, idx) => {
      if (idx !== i) return c
      const updated = { ...c, ...updates }
      if (updates.field) updated.operator = defaultOp(updates.field)
      return updated
    }))
    setPreview(null)
  }

  function removeCondition(i: number) {
    setConditions(prev => prev.filter((_, idx) => idx !== i))
    setPreview(null)
  }

  function buildRules() {
    return {
      operator,
      conditions: conditions.map(c => ({
        field: c.field,
        operator: c.operator,
        value: ['in', 'not_in'].includes(c.operator)
          ? c.value.split(',').map(v => v.trim()).filter(Boolean)
          : isNaN(Number(c.value)) ? c.value : Number(c.value),
      })),
    }
  }

  async function handlePreview() {
    setPreviewing(true)
    try {
      const res = await previewSegment(buildRules())
      setPreview(res)
    } catch { alert('Preview failed') }
    finally { setPreviewing(false) }
  }

  async function handleSave() {
    if (!name.trim()) return alert('Enter a segment name')
    setSaving(true)
    try {
      await createSegment({ name, description: desc, rules: buildRules() })
      setShowBuilder(false)
      setName(''); setDesc(''); setPreview(null)
      setConditions([{ field: 'total_spent', operator: 'gte', value: '5000' }])
      load()
    } catch { alert('Failed to save segment') }
    finally { setSaving(false) }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this segment?')) return
    await deleteSegment(id)
    if (selected?.id === id) { setSelected(null); setCustomers([]) }
    load()
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Segments</h1>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/copilot')}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-700 hover:border-violet-600/60 text-gray-300 hover:text-white text-sm rounded-lg transition-all"
          >
            <Bot size={14} className="text-violet-400" />
            Build with AI
          </button>
          <button
            onClick={() => setShowBuilder(true)}
            className="flex items-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm rounded-lg transition-colors"
          >
            <Plus size={14} />
            New Segment
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Segment list */}
        <div className="space-y-2">
          {segments.map(seg => (
            <div
              key={seg.id}
              onClick={() => selectSegment(seg)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                selected?.id === seg.id
                  ? 'bg-violet-600/10 border-violet-600/50'
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-white flex items-center gap-2">
                    {seg.name}
                    {seg.created_by_ai && (
                      <span className="text-xs bg-violet-600/20 text-violet-400 px-1.5 py-0.5 rounded">AI</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{seg.description}</p>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); handleDelete(seg.id) }}
                  className="text-gray-600 hover:text-red-400 transition-colors p-1"
                >
                  <Trash2 size={13} />
                </button>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <Users size={12} className="text-gray-500" />
                <span className="text-xs text-gray-500">{seg.customer_count} customers</span>
              </div>
            </div>
          ))}
          {segments.length === 0 && (
            <div className="text-center py-12 text-gray-600 text-sm">
              No segments yet. Create one above or ask the AI Copilot.
            </div>
          )}
        </div>

        {/* Segment customers */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="bg-gray-800 rounded-xl border border-gray-700">
              <div className="px-5 py-4 border-b border-gray-700">
                <p className="text-sm font-semibold text-white">{selected.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{customers.length} customers matched</p>
              </div>
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-800">
                    <tr className="text-gray-500 text-xs uppercase border-b border-gray-700">
                      <th className="text-left px-5 py-3">Name</th>
                      <th className="text-left px-5 py-3">City</th>
                      <th className="text-right px-5 py-3">Orders</th>
                      <th className="text-right px-5 py-3">Total Spent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customers.map(c => (
                      <tr key={c.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                        <td className="px-5 py-2.5 text-white text-xs">{c.name}</td>
                        <td className="px-5 py-2.5 text-gray-400 text-xs">{c.city ?? '—'}</td>
                        <td className="px-5 py-2.5 text-right text-gray-400 text-xs">{c.total_orders}</td>
                        <td className="px-5 py-2.5 text-right text-gray-300 text-xs font-medium">
                          ₹{c.total_spent.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 bg-gray-800 rounded-xl border border-gray-700 border-dashed">
              <p className="text-gray-600 text-sm">Select a segment to view its customers</p>
            </div>
          )}
        </div>
      </div>

      {/* Rule builder modal */}
      {showBuilder && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-2xl shadow-2xl">
            <div className="px-6 py-5 border-b border-gray-800">
              <h2 className="text-base font-semibold text-white">Build Segment</h2>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Segment Name</label>
                  <input
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="e.g. High-Value Mumbai"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Description</label>
                  <input
                    value={desc}
                    onChange={e => setDesc(e.target.value)}
                    placeholder="Optional description"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-violet-600"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">Match</span>
                {(['AND', 'OR'] as const).map(op => (
                  <button
                    key={op}
                    onClick={() => setOperator(op)}
                    className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                      operator === op
                        ? 'bg-violet-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white border border-gray-700'
                    }`}
                  >
                    {op}
                  </button>
                ))}
                <span className="text-xs text-gray-500">of the following conditions</span>
              </div>

              <div className="space-y-2">
                {conditions.map((c, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <select
                      value={c.field}
                      onChange={e => updateCondition(i, { field: e.target.value })}
                      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white outline-none flex-shrink-0"
                    >
                      {FIELD_OPTIONS.map(f => (
                        <option key={f.value} value={f.value}>{f.label}</option>
                      ))}
                    </select>
                    <select
                      value={c.operator}
                      onChange={e => updateCondition(i, { operator: e.target.value })}
                      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white outline-none flex-shrink-0"
                    >
                      {(OP_MAP[c.field] ?? ['gte']).map(op => (
                        <option key={op} value={op}>{op}</option>
                      ))}
                    </select>
                    <input
                      value={c.value}
                      onChange={e => updateCondition(i, { value: e.target.value })}
                      placeholder={c.field === 'city' ? 'Mumbai, Delhi' : 'value'}
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-violet-600"
                    />
                    <button onClick={() => removeCondition(i)} className="text-gray-600 hover:text-red-400 p-1">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
                <button
                  onClick={addCondition}
                  className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 mt-1"
                >
                  <Plus size={12} /> Add condition
                </button>
              </div>

              {preview && (
                <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                  <p className="text-sm font-medium text-white">
                    {preview.matching_count} customers matched
                  </p>
                  {preview.sample.length > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      e.g. {preview.sample.slice(0, 3).map(c => c.name).join(', ')}
                      {preview.matching_count > 3 ? ` and ${preview.matching_count - 3} more` : ''}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-gray-800 flex gap-3 justify-end">
              <button
                onClick={() => setShowBuilder(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePreview}
                disabled={previewing}
                className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {previewing ? 'Previewing…' : 'Preview'}
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save Segment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
