import { Upload, UserPlus } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Customer, getCustomers, importCustomersCSV } from '../lib/api'

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [search, setSearch]       = useState('')
  const [city, setCity]           = useState('')
  const [importing, setImporting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  function load() {
    getCustomers(city || undefined).then(setCustomers)
  }

  useEffect(() => { load() }, [city])

  const filtered = customers.filter(c => {
    const q = search.toLowerCase()
    return (
      c.name.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      (c.city ?? '').toLowerCase().includes(q)
    )
  })

  const cities = [...new Set(customers.map(c => c.city).filter(Boolean))] as string[]

  async function handleCSV(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    try {
      const res = await importCustomersCSV(file)
      alert(`Import complete: ${res.created} added, ${res.skipped} skipped.`)
      load()
    } catch {
      alert('Import failed. Check CSV format.')
    } finally {
      setImporting(false)
      e.target.value = ''
    }
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Customers</h1>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={importing}
          className="flex items-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
        >
          <Upload size={14} />
          {importing ? 'Importing…' : 'Import CSV'}
        </button>
        <input ref={fileRef} type="file" accept=".csv" onChange={handleCSV} className="hidden" />
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by name or email…"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-violet-600"
        />
        <select
          value={city}
          onChange={e => setCity(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 outline-none focus:border-violet-600"
        >
          <option value="">All cities</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-700 text-xs text-gray-500">
          {filtered.length} customers
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase border-b border-gray-700">
                <th className="text-left px-5 py-3">Name</th>
                <th className="text-left px-5 py-3">Email</th>
                <th className="text-left px-5 py-3">City</th>
                <th className="text-right px-5 py-3">Orders</th>
                <th className="text-right px-5 py-3">Total Spent</th>
                <th className="text-left px-5 py-3">Last Order</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="px-5 py-3 font-medium text-white">{c.name}</td>
                  <td className="px-5 py-3 text-gray-400">{c.email}</td>
                  <td className="px-5 py-3 text-gray-400">{c.city ?? '—'}</td>
                  <td className="px-5 py-3 text-right text-gray-400">{c.total_orders}</td>
                  <td className="px-5 py-3 text-right text-gray-300 font-medium">
                    ₹{c.total_spent.toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-gray-500 text-xs">
                    {c.last_order_date
                      ? new Date(c.last_order_date).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', year: 'numeric',
                        })
                      : '—'}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-gray-600">
                    No customers match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CSV format hint */}
      <p className="text-xs text-gray-600">
        CSV import expects columns: <code className="text-gray-500">name, email, phone, city</code>
      </p>
    </div>
  )
}
