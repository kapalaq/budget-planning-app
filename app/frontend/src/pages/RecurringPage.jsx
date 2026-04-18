import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import AmountInput from '../components/AmountInput'
import { Repeat, Trash2, Plus, Send } from 'lucide-react'

const FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
]

const WEEKDAYS = [
  { value: 0, label: 'Mon' },
  { value: 1, label: 'Tue' },
  { value: 2, label: 'Wed' },
  { value: 3, label: 'Thu' },
  { value: 4, label: 'Fri' },
  { value: 5, label: 'Sat' },
  { value: 6, label: 'Sun' },
]

function RecurrenceRuleForm({ rule, onChange }) {
  return (
    <>
      <div className="form-group">
        <label>Frequency</label>
        <select className="form-input" value={rule.frequency} onChange={(e) => onChange({ ...rule, frequency: e.target.value })}>
          {FREQUENCIES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
      </div>
      <div className="form-group">
        <label>Interval</label>
        <input type="number" min="1" className="form-input" value={rule.interval} onChange={(e) => onChange({ ...rule, interval: parseInt(e.target.value) || 1 })} />
      </div>
      {rule.frequency === 'weekly' && (
        <div className="form-group">
          <label>Days of Week</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {WEEKDAYS.map((wd) => (
              <button
                key={wd.value}
                type="button"
                className={`btn btn-sm ${(rule.weekdays || []).includes(wd.value) ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => {
                  const cur = rule.weekdays || []
                  const next = cur.includes(wd.value) ? cur.filter((v) => v !== wd.value) : [...cur, wd.value]
                  onChange({ ...rule, weekdays: next })
                }}
              >
                {wd.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

export default function RecurringPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [showAddTransfer, setShowAddTransfer] = useState(false)
  const [categories, setCategories] = useState([])
  const [transferCtx, setTransferCtx] = useState(null)
  const [saving, setSaving] = useState(false)
  const { toasts, success, error: showError } = useToast()

  const defaultForm = { transaction_type: '-', category: '', amount: '', description: '', start_date: '', recurrence_rule: { frequency: 'monthly', interval: 1, weekdays: [] } }
  const [form, setForm] = useState(defaultForm)
  const defaultTransferForm = { target_wallet_name: '', amount: '', description: '', start_date: '', recurrence_rule: { frequency: 'monthly', interval: 1, weekdays: [] } }
  const [transferForm, setTransferForm] = useState(defaultTransferForm)

  const load = useCallback(async () => {
    try {
      const res = await api.getRecurringList()
      setItems(res.data?.recurring_transactions || [])
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

  const openAdd = async () => {
    try {
      const res = await api.getCategories(form.transaction_type === '+' ? 'income' : 'expense')
      setCategories(res.data?.categories || [])
      setForm(defaultForm)
      setShowAdd(true)
    } catch (err) { showError(err.message) }
  }

  const handleTypeChange = async (type) => {
    try {
      const res = await api.getCategories(type === '+' ? 'income' : 'expense')
      setCategories(res.data?.categories || [])
      setForm({ ...form, transaction_type: type, category: '' })
    } catch (err) { showError(err.message) }
  }

  const handleAddRecurring = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const recurringPayload = {
        transaction_type: form.transaction_type,
        category: form.category,
        amount: parseFloat(form.amount),
        description: form.description,
        recurrence_rule: form.recurrence_rule,
      }
      if (form.start_date) {
        const parts = form.start_date.replace('T', ' ')
        recurringPayload.start_date = parts.length <= 16 ? parts + ':00' : parts
      }
      await api.addRecurring(recurringPayload)
      success('Recurring transaction created')
      setShowAdd(false)
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const openAddTransfer = async () => {
    try {
      const res = await api.getTransferContext()
      const d = res.data
      setTransferCtx({
        current_wallet: d.from_wallet?.name || '',
        currency: d.from_wallet?.currency || '',
        available_wallets: (d.target_wallets || []).map((w) => w.name),
      })
      setTransferForm(defaultTransferForm)
      setShowAddTransfer(true)
    } catch (err) { showError(err.message) }
  }

  const handleAddTransfer = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const transferPayload = {
        target_wallet_name: transferForm.target_wallet_name,
        amount: parseFloat(transferForm.amount),
        description: transferForm.description,
        recurrence_rule: transferForm.recurrence_rule,
      }
      if (transferForm.start_date) {
        const parts2 = transferForm.start_date.replace('T', ' ')
        transferPayload.start_date = parts2.length <= 16 ? parts2 + ':00' : parts2
      }
      await api.addRecurringTransfer(transferPayload)
      success('Recurring transfer created')
      setShowAddTransfer(false)
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div className="page-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Recurring</h2>
          <div className="page-header-actions" style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={openAddTransfer}>
              <Send size={14} /> Transfer
            </button>
            <button className="btn btn-primary btn-sm" onClick={openAdd}>
              <Plus size={16} /> Add
            </button>
          </div>
        </div>
      </div>
      <div className="page-content fade-in">
        {items.length === 0 ? (
          <EmptyState icon={Repeat} title="No recurring transactions" description="Add a recurring transaction to automate your finances" />
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

      {showAdd && (
        <Modal title="Add Recurring Transaction" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAddRecurring}>
            <div className="form-group">
              <label>Type</label>
              <div className="type-tabs" style={{ marginBottom: 4 }}>
                <button type="button" className={`type-tab ${form.transaction_type === '-' ? 'active' : ''}`} onClick={() => handleTypeChange('-')}>Expense</button>
                <button type="button" className={`type-tab ${form.transaction_type === '+' ? 'active' : ''}`} onClick={() => handleTypeChange('+')}>Income</button>
              </div>
            </div>
            <div className="form-group">
              <label>Category</label>
              <select className="form-input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required>
                <option value="">Select category</option>
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Amount</label>
              <AmountInput value={form.amount} onChange={(v) => setForm({ ...form, amount: v })} required />
            </div>
            <div className="form-group">
              <label>Start Date & Time</label>
              <input type="datetime-local" className="form-input" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <RecurrenceRuleForm rule={form.recurrence_rule} onChange={(rule) => setForm({ ...form, recurrence_rule: rule })} />
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showAddTransfer && transferCtx && (
        <Modal title="Add Recurring Transfer" onClose={() => setShowAddTransfer(false)}>
          <form onSubmit={handleAddTransfer}>
            <div style={{ padding: '10px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.85rem' }}>
              From: <strong>{transferCtx.current_wallet}</strong> ({transferCtx.currency})
            </div>
            <div className="form-group">
              <label>To Wallet</label>
              <select className="form-input" value={transferForm.target_wallet_name} onChange={(e) => setTransferForm({ ...transferForm, target_wallet_name: e.target.value })} required>
                <option value="">Select wallet</option>
                {(transferCtx.available_wallets || []).map((w) => <option key={w} value={w}>{w}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Amount</label>
              <AmountInput value={transferForm.amount} onChange={(v) => setTransferForm({ ...transferForm, amount: v })} required />
            </div>
            <div className="form-group">
              <label>Start Date & Time</label>
              <input type="datetime-local" className="form-input" value={transferForm.start_date} onChange={(e) => setTransferForm({ ...transferForm, start_date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={transferForm.description} onChange={(e) => setTransferForm({ ...transferForm, description: e.target.value })} />
            </div>
            <RecurrenceRuleForm rule={transferForm.recurrence_rule} onChange={(rule) => setTransferForm({ ...transferForm, recurrence_rule: rule })} />
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAddTransfer(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
