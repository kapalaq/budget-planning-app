import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import { Target, Plus, Trash2, DollarSign, CheckCircle, EyeOff, RotateCcw } from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function GoalsPage() {
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [showSave, setShowSave] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [newGoal, setNewGoal] = useState({ name: '', target_amount: '', currency: 'USD', description: '' })
  const [saveAmount, setSaveAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [filter, setFilter] = useState('active')
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = filter === 'all' ? await api.getAllGoals() : await api.getGoals(filter)
      setGoals(res.data?.goals || [])
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError, filter])

  useEffect(() => { load() }, [load])

  const handleAdd = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.addGoal({ ...newGoal, target_amount: parseFloat(newGoal.target_amount) })
      success('Goal created')
      setShowAdd(false)
      setNewGoal({ name: '', target_amount: '', currency: 'USD', description: '' })
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.saveToGoal({ name: showSave, amount: parseFloat(saveAmount) })
      success(`Saved to ${showSave}`)
      setShowSave(null)
      setSaveAmount('')
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleComplete = async (name) => {
    try {
      await api.completeGoal(name)
      success(`${name} completed!`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleHide = async (name) => {
    try {
      await api.hideGoal(name)
      success(`${name} hidden`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleReactivate = async (name) => {
    try {
      await api.reactivateGoal(name)
      success(`${name} reactivated`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleDelete = async () => {
    try {
      await api.deleteGoal(deleteTarget)
      success('Goal deleted')
      setDeleteTarget(null)
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Savings Goals</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <div className="type-tabs">
              {['active', 'all'].map((f) => (
                <button key={f} className={`type-tab ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
              <Plus size={18} /> Add Goal
            </button>
          </div>
        </div>
      </div>
      <div className="page-content fade-in">
        {goals.length === 0 ? (
          <EmptyState icon={Target} title="No goals" description="Create a savings goal to start tracking" />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {goals.map((g) => (
              <div key={g.name} className="goal-card">
                <div className="goal-header">
                  <div className="goal-name">{g.name}</div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span className={`badge ${g.status === 'active' ? 'active' : g.status === 'completed' ? 'income' : 'inactive'}`}>
                      {g.status}
                    </span>
                  </div>
                </div>
                {g.description && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8 }}>{g.description}</div>}
                <div className="progress-bar" style={{ marginBottom: 8 }}>
                  <div className={`fill ${g.progress >= 100 ? 'complete' : g.progress >= 75 ? 'warning' : ''}`} style={{ width: `${Math.min(g.progress, 100)}%` }} />
                </div>
                <div className="goal-amounts">
                  <span>{formatAmount(g.saved, g.currency)} saved</span>
                  <span>{formatAmount(g.target, g.currency)} target</span>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  {g.status === 'active' && (
                    <>
                      <button className="btn btn-primary btn-sm" onClick={() => { setShowSave(g.name); setSaveAmount('') }}>
                        <DollarSign size={14} /> Save
                      </button>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleComplete(g.name)}>
                        <CheckCircle size={14} /> Complete
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleHide(g.name)} title="Hide (allows deletion)">
                        <EyeOff size={14} />
                      </button>
                    </>
                  )}
                  {g.status === 'hidden' && (
                    <button className="btn btn-secondary btn-sm" onClick={() => handleReactivate(g.name)}>
                      <RotateCcw size={14} /> Reactivate
                    </button>
                  )}
                  {g.status !== 'active' && (
                    <button className="btn btn-ghost btn-sm" onClick={() => setDeleteTarget(g.name)}>
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showAdd && (
        <Modal title="New Goal" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd}>
            <div className="form-group">
              <label>Name</label>
              <input className="form-input" value={newGoal.name} onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })} required autoFocus />
            </div>
            <div className="form-group">
              <label>Target Amount</label>
              <input type="number" step="0.01" min="0" className="form-input" value={newGoal.target_amount} onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <select className="form-input" value={newGoal.currency} onChange={(e) => setNewGoal({ ...newGoal, currency: e.target.value })}>
                {['USD', 'EUR', 'GBP', 'KZT', 'RUB', 'JPY', 'CNY'].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={newGoal.description} onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showSave && (
        <Modal title={`Save to ${showSave}`} onClose={() => setShowSave(null)}>
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label>Amount</label>
              <input type="number" step="0.01" min="0" className="form-input" value={saveAmount} onChange={(e) => setSaveAmount(e.target.value)} required autoFocus />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowSave(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog title="Delete Goal" message={`Delete "${deleteTarget}" and all saved progress?`} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} danger />
      )}
    </>
  )
}
