import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import AmountInput from '../components/AmountInput'
import { Target, Plus, Trash2, PiggyBank, ShoppingCart, CheckCircle, EyeOff, RotateCcw, ArrowLeftRight } from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function GoalsPage() {
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [showReserve, setShowReserve] = useState(null)
  const [showSpend, setShowSpend] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [newGoal, setNewGoal] = useState({ name: '', target_amount: '', currency: 'USD', description: '' })
  const [reserveAmount, setReserveAmount] = useState('')
  const [spendForm, setSpendForm] = useState({ amount: '', category: '', description: '' })
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
      await api.addGoal({ ...newGoal, target: parseFloat(newGoal.target_amount) })
      success('Goal created')
      setShowAdd(false)
      setNewGoal({ name: '', target_amount: '', currency: 'USD', description: '' })
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleReserve = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.saveToGoal({ goal_name: showReserve, amount: parseFloat(reserveAmount) })
      success(`Reserved for ${showReserve}`)
      setShowReserve(null)
      setReserveAmount('')
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleSpend = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.spendFromGoal({
        goal_name: showSpend,
        amount: parseFloat(spendForm.amount),
        category: spendForm.category || 'Goal Expense',
        description: spendForm.description,
      })
      success(`Expense added to ${showSpend}`)
      setShowSpend(null)
      setSpendForm({ amount: '', category: '', description: '' })
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

  const handleConvertToBill = async (name) => {
    try {
      await api.convertGoalToBill(name)
      success(`Converted to bill`)
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
        <div className="page-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Savings Goals</h2>
          <div className="page-header-actions" style={{ display: 'flex', gap: 8 }}>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(300px, 100%), 1fr))', gap: 16 }}>
            {goals.map((g) => {
              const gd = g.goal || {}
              const status = gd.status || 'active'
              const displayName = g.name.replace(/^Goal:\s*/, '')
              const reserved = gd.reserved ?? gd.saved ?? 0
              const spent = gd.spent ?? 0
              const totalReserved = gd.saved ?? 0
              return (
                <div key={g.name} className="goal-card">
                  <div className="goal-header">
                    <div className="goal-name">{displayName}</div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <span className={`badge ${status === 'active' ? 'active' : status === 'completed' ? 'income' : 'inactive'}`}>
                        {status}
                      </span>
                    </div>
                  </div>
                  {g.description && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8 }}>{g.description}</div>}
                  <div className="progress-bar" style={{ marginBottom: 8 }}>
                    <div className={`fill ${gd.progress >= 100 ? 'complete' : gd.progress >= 75 ? 'warning' : ''}`} style={{ width: `${Math.min(gd.progress || 0, 100)}%` }} />
                  </div>
                  <div className="goal-amounts" style={{ marginBottom: 4 }}>
                    <span>{formatAmount(totalReserved, g.currency)} reserved</span>
                    <span>{formatAmount(gd.target, g.currency)} target</span>
                  </div>
                  <div style={{ display: 'flex', gap: 12, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span>Available: {formatAmount(reserved, g.currency)}</span>
                    {spent > 0 && <span>Spent: {formatAmount(spent, g.currency)}</span>}
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                    {status === 'active' && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => { setShowReserve(g.name); setReserveAmount('') }}>
                          <PiggyBank size={14} /> Reserve
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => { setShowSpend(g.name); setSpendForm({ amount: '', category: '', description: '' }) }}>
                          <ShoppingCart size={14} /> Spend
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => handleComplete(g.name)}>
                          <CheckCircle size={14} /> Complete
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={() => handleConvertToBill(g.name)} title="Convert to bill">
                          <ArrowLeftRight size={14} />
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={() => handleHide(g.name)} title="Hide (allows deletion)">
                          <EyeOff size={14} />
                        </button>
                      </>
                    )}
                    {status === 'hidden' && (
                      <button className="btn btn-secondary btn-sm" onClick={() => handleReactivate(g.name)}>
                        <RotateCcw size={14} /> Reactivate
                      </button>
                    )}
                    {status !== 'active' && (
                      <button className="btn btn-ghost btn-sm" onClick={() => setDeleteTarget(g.name)}>
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
        <Modal title="New Goal" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd}>
            <div className="form-group">
              <label>Name</label>
              <input className="form-input" value={newGoal.name} onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })} required autoFocus />
            </div>
            <div className="form-group">
              <label>Target Amount</label>
              <AmountInput value={newGoal.target_amount} onChange={(v) => setNewGoal({ ...newGoal, target_amount: v })} required />
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

      {showReserve && (
        <Modal title={`Reserve money for ${showReserve.replace(/^Goal:\s*/, '')}`} onClose={() => setShowReserve(null)}>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 12 }}>
            Transfer money from your active wallet into this goal for safekeeping.
          </p>
          <form onSubmit={handleReserve}>
            <div className="form-group">
              <label>Amount</label>
              <AmountInput value={reserveAmount} onChange={setReserveAmount} required autoFocus />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowReserve(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Reserving...' : 'Reserve'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showSpend && (
        <Modal title={`Spend from ${showSpend.replace(/^Goal:\s*/, '')}`} onClose={() => setShowSpend(null)}>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 12 }}>
            Record a purchase made using this goal&apos;s reserved funds. If not enough is reserved, the shortfall is automatically pulled from your active wallet.
          </p>
          <form onSubmit={handleSpend}>
            <div className="form-group">
              <label>Amount</label>
              <AmountInput value={spendForm.amount} onChange={(v) => setSpendForm({ ...spendForm, amount: v })} required autoFocus />
            </div>
            <div className="form-group">
              <label>Category</label>
              <input className="form-input" placeholder="e.g. Flights, Hotel, Shopping" value={spendForm.category} onChange={(e) => setSpendForm({ ...spendForm, category: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={spendForm.description} onChange={(e) => setSpendForm({ ...spendForm, description: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowSpend(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Add Expense'}</button>
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
