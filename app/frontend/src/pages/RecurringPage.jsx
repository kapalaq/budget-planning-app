import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import { Repeat, Trash2 } from 'lucide-react'

export default function RecurringPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = await api.getRecurringList()
      setItems(res.data?.recurring || [])
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError])

  useEffect(() => { load() }, [load])

  const handleDelete = async () => {
    try {
      await api.deleteRecurring(deleteTarget)
      success('Recurring transaction deleted')
      setDeleteTarget(null)
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header"><h2>Recurring Transactions</h2></div>
      <div className="page-content fade-in">
        {items.length === 0 ? (
          <EmptyState icon={Repeat} title="No recurring transactions" description="Recurring transactions can be added from the CLI or Telegram bot" />
        ) : (
          <div className="card">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {items.map((r, idx) => (
                <div key={r.id} className="recurring-row">
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      {r.category}
                      {r.description && <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: 8 }}>{r.description}</span>}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{r.pattern_description}</div>
                  </div>
                  <div className={`transaction-amount ${r.transaction_type}`}>
                    {r.sign}{Number(r.amount).toLocaleString()}
                  </div>
                  <div>
                    <span className={`badge ${r.is_active ? 'active' : 'inactive'}`}>
                      {r.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <button className="btn-icon" onClick={() => setDeleteTarget(idx)}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {deleteTarget !== null && (
        <ConfirmDialog title="Delete Recurring" message="Delete this recurring transaction?" onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} danger />
      )}
    </>
  )
}
