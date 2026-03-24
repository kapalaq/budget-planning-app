import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import { Wallet, Plus, Trash2, Check, CreditCard, ArrowUpDown } from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function WalletsPage() {
  const [wallets, setWallets] = useState([])
  const [currentWallet, setCurrentWallet] = useState('')
  const [sortingStrategy, setSortingStrategy] = useState('')
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [newWallet, setNewWallet] = useState({ name: '', currency: 'USD', description: '' })
  const [saving, setSaving] = useState(false)
  const [showSortModal, setShowSortModal] = useState(false)
  const [sortOptions, setSortOptions] = useState(null)
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = await api.getWallets()
      setWallets(res.data?.wallets || [])
      setCurrentWallet(res.data?.current_wallet_name || res.data?.current_wallet || '')
      setSortingStrategy(res.data?.sorting_strategy || '')
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError])

  useEffect(() => { load() }, [load])

  const handleSwitch = async (name) => {
    try {
      await api.switchWallet(name)
      success(`Switched to ${name}`)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.addWallet(newWallet)
      success('Wallet created')
      setShowAdd(false)
      setNewWallet({ name: '', currency: 'USD', description: '' })
      load()
    } catch (err) { showError(err.message) }
    finally { setSaving(false) }
  }

  const handleDelete = async () => {
    try {
      await api.deleteWallet(deleteTarget)
      success('Wallet deleted')
      setDeleteTarget(null)
      load()
    } catch (err) { showError(err.message) }
  }

  const openSortModal = async () => {
    try {
      const res = await api.getWalletSortingOptions()
      setSortOptions(res.data?.options || {})
      setShowSortModal(true)
    } catch (err) { showError(err.message) }
  }

  const handleSetSorting = async (key) => {
    try {
      await api.setWalletSorting({ strategy_key: key })
      success('Sorting updated')
      setShowSortModal(false)
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Wallets</h2>
            {sortingStrategy && <p>Sorted: {sortingStrategy}</p>}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={openSortModal}>
              <ArrowUpDown size={14} /> Sort
            </button>
            <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
              <Plus size={18} /> Add Wallet
            </button>
          </div>
        </div>
      </div>
      <div className="page-content fade-in">
        {wallets.length === 0 ? (
          <EmptyState icon={CreditCard} title="No wallets" description="Create your first wallet" />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {wallets.map((w) => (
              <div key={w.name} className={`wallet-card ${w.name === currentWallet ? 'active' : ''}`} onClick={() => handleSwitch(w.name)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div className="name">
                    <Wallet size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 6 }} />
                    {w.name}
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {w.name === currentWallet && <span className="badge active"><Check size={10} /> Active</span>}
                    {w.name !== currentWallet && (
                      <button className="btn-icon" onClick={(e) => { e.stopPropagation(); setDeleteTarget(w.name) }} title="Delete">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
                <div className="balance">{formatAmount(w.balance, w.currency)}</div>
                <div className="meta">
                  <span>{w.transaction_count} transactions</span>
                  <span>{w.currency}</span>
                  {w.wallet_type !== 'standard' && <span className="badge transfer">{w.wallet_type}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showAdd && (
        <Modal title="New Wallet" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd}>
            <div className="form-group">
              <label>Name</label>
              <input className="form-input" value={newWallet.name} onChange={(e) => setNewWallet({ ...newWallet, name: e.target.value })} required autoFocus />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <select className="form-input" value={newWallet.currency} onChange={(e) => setNewWallet({ ...newWallet, currency: e.target.value })}>
                {['USD', 'EUR', 'GBP', 'KZT', 'RUB', 'JPY', 'CNY', 'TRY', 'BRL', 'INR'].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input className="form-input" value={newWallet.description} onChange={(e) => setNewWallet({ ...newWallet, description: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog title="Delete Wallet" message={`Delete "${deleteTarget}" and all its transactions?`} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} danger />
      )}

      {showSortModal && sortOptions && (
        <Modal title="Sort Wallets" onClose={() => setShowSortModal(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(sortOptions).map(([key, name]) => (
              <button
                key={key}
                className={`btn ${sortingStrategy === name ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => handleSetSorting(key)}
              >
                {sortingStrategy === name && <span style={{ marginRight: 6 }}>&#10003;</span>}
                {name}
              </button>
            ))}
          </div>
          <div className="modal-actions" style={{ marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={() => setShowSortModal(false)}>Close</button>
          </div>
        </Modal>
      )}
    </>
  )
}
