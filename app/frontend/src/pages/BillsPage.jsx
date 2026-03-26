import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import AmountInput from '../components/AmountInput'
import { Receipt, Plus, Trash2, DollarSign, CheckCircle, EyeOff, RotateCcw } from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function BillsPage() {
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [showSave, setShowSave] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [newBill, setNewBill] = useState({ name: '', target_amount: '', currency: 'USD', description: '' })
  const [saveAmount, setSaveAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [filter, setFilter] = useState('active')
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = filter === 'all' ? await api.getAllBills() : await api.getBills(filter)
      setBills(res.data?.bills || [])
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError, filter])

  useEffect(() => { load() }, [load])

  const handleAdd = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.addBill({ ...newBill, target: parseFloat(newBill.target_amount) })
      success('Bill created')
      setShowAdd(false)
      setNewBill({ name: '', target_amount: '', currency: 'USD', description: '' })
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.saveToBill({ bill_name: showSave, amount: parseFloat(saveAmount) })
      success(`Saved to ${showSave}`)
      setShowSave(null)
      setSaveAmount('')
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleComplete = async (name) => {
    try {
      await api.completeBill(name)
      success(`${name} completed!`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleHide = async (name) => {
    try {
      await api.hideBill(name)
      success(`${name} hidden`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleReactivate = async (name) => {
    try {
      await api.reactivateBill(name)
      success(`${name} reactivated`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleDelete = async () => {
    try {
      await api.deleteBill(deleteTarget)
      success('Bill deleted')
      setDeleteTarget(null)
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div className="page-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Bills</h2>
          <div className="page-header-actions" style={{ display: 'flex', gap: 8 }}>
            <div className="type-tabs">
              {['active', 'all'].map((f) => (
                <button key={f} className={`type-tab ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
              <Plus size={18} /> Add Bill
            </button>
          </div>
        </div>
      </div>
      <div className="page-content fade-in">
        {bills.length === 0 ? (
          <EmptyState icon={Receipt} title="No bills" description="Add a bill to start tracking" />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(300px, 100%), 1fr))', gap: 16 }}>
            {bills.map((b) => {
              const bd = b.bill || {}
              const status = bd.status || 'active'
              const displayName = b.name.replace(/^Bill:\s*/, '')
              return (
                <div key={b.name} className="goal-card">
                  <div className="goal-header">
                    <div className="goal-name">{displayName}</div>
                    <span className={`badge ${status === 'active' ? 'active' : status === 'completed' ? 'income' : 'inactive'}`}>
                      {status}
                    </span>
                  </div>
                  {b.description && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8 }}>{b.description}</div>}
                  <div className="progress-bar" style={{ marginBottom: 8 }}>
                    <div className={`fill ${bd.progress >= 100 ? 'complete' : bd.progress >= 75 ? 'warning' : ''}`} style={{ width: `${Math.min(bd.progress || 0, 100)}%` }} />
                  </div>
                  <div className="goal-amounts">
                    <span>{formatAmount(bd.saved, b.currency)} saved</span>
                    <span>{formatAmount(bd.target, b.currency)} due</span>
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                    {status === 'active' && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => { setShowSave(b.name); setSaveAmount('') }}>
                          <DollarSign size={14} /> Pay
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => handleComplete(b.name)}>
                          <CheckCircle size={14} /> Complete
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={() => handleHide(b.name)} title="Hide (allows deletion)">
                          <EyeOff size={14} />
                        </button>
                      </>
                    )}
                    {status === 'hidden' && (
                      <button className="btn btn-secondary btn-sm" onClick={() => handleReactivate(b.name)}>
                        <RotateCcw size={14} /> Reactivate
                      </button>
                    )}
                    {status !== 'active' && (
                      <button className="btn btn-ghost btn-sm" onClick={() => setDeleteTarget(b.name)}>
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {showAdd && (
        <Modal title="New Bill" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd}>
            <div className="form-group">
              <label>Name</label>
              <input className="form-input" value={newBill.name} onChange={(e) => setNewBill({ ...newBill, name: e.target.value })} required autoFocus />
            </div>
            <div className="form-group">
              <label>Amount Due</label>
              <AmountInput value={newBill.target_amount} onChange={(v) => setNewBill({ ...newBill, target_amount: v })} required />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <select className="form-input" value={newBill.currency} onChange={(e) => setNewBill({ ...newBill, currency: e.target.value })}>
                {['USD', 'EUR', 'GBP', 'KZT', 'RUB', 'JPY', 'CNY'].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={newBill.description} onChange={(e) => setNewBill({ ...newBill, description: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showSave && (
        <Modal title={`Pay ${showSave}`} onClose={() => setShowSave(null)}>
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label>Amount</label>
              <AmountInput value={saveAmount} onChange={setSaveAmount} required autoFocus />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowSave(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Paying...' : 'Pay'}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog title="Delete Bill" message={`Delete "${deleteTarget}"?`} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} danger />
      )}
    </>
  )
}
