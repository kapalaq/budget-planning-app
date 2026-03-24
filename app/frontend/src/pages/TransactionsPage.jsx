import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import TransactionForm from '../components/TransactionForm'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ConfirmDialog'
import {
  Plus, Trash2, Edit3, ArrowLeftRight, Send, Filter, X,
} from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function TransactionsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTx, setShowAddTx] = useState(false)
  const [showTransfer, setShowTransfer] = useState(false)
  const [editTx, setEditTx] = useState(null)
  const [deleteTx, setDeleteTx] = useState(null)
  const [transferCtx, setTransferCtx] = useState(null)
  const [transferData, setTransferData] = useState({ to_wallet: '', amount: '', received_amount: '' })
  const [transferLoading, setTransferLoading] = useState(false)
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = await api.getDashboard()
      setData(res.data)
    } catch (err) {
      showError(err.message)
    } finally {
      setLoading(false)
    }
  }, [showError])

  useEffect(() => { load() }, [load])

  const handleAdd = async (txData) => {
    try {
      await api.addTransaction(txData)
      success('Transaction added')
      setShowAddTx(false)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleEdit = async (txData) => {
    try {
      const foundIdx = data.transactions.findIndex((t) => t.id === editTx.id)
      if (foundIdx === -1) return
      const idx = foundIdx + 1
      await api.editTransaction(idx, txData)
      success('Transaction updated')
      setEditTx(null)
      load()
    } catch (err) { showError(err.message) }
  }

  const handleDelete = async () => {
    try {
      const foundIdx = data.transactions.findIndex((t) => t.id === deleteTx.id)
      if (foundIdx === -1) return
      const idx = foundIdx + 1
      await api.deleteTransaction(idx)
      success('Transaction deleted')
      setDeleteTx(null)
      load()
    } catch (err) { showError(err.message) }
  }

  const openTransfer = async () => {
    try {
      const res = await api.getTransferContext()
      const d = res.data
      setTransferCtx({
        current_wallet: d.from_wallet?.name || '',
        currency: d.from_wallet?.currency || '',
        target_wallets: d.target_wallets || [],
      })
      setTransferData({ to_wallet: '', amount: '', received_amount: '' })
      setShowTransfer(true)
    } catch (err) { showError(err.message) }
  }

  const handleTransfer = async (e) => {
    e.preventDefault()
    setTransferLoading(true)
    try {
      const transferPayload = {
        target_wallet_name: transferData.to_wallet,
        amount: parseFloat(transferData.amount),
      }
      if (transferData.received_amount) {
        transferPayload.received_amount = parseFloat(transferData.received_amount)
      }
      await api.transfer(transferPayload)
      success('Transfer completed')
      setShowTransfer(false)
      load()
    } catch (err) { showError(err.message) }
    finally { setTransferLoading(false) }
  }

  const handleClearFilters = async () => {
    try {
      await api.clearFilters()
      success('Filters cleared')
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>
  if (!data) return null

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Transactions</h2>
            <p>{data.wallet_name} - {data.currency}</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {data.has_filters && (
              <button className="btn btn-secondary btn-sm" onClick={handleClearFilters}>
                <X size={14} /> Clear Filters
              </button>
            )}
            <button className="btn btn-secondary" onClick={openTransfer}>
              <Send size={16} /> Transfer
            </button>
            <button className="btn btn-primary" onClick={() => setShowAddTx(true)}>
              <Plus size={18} /> Add
            </button>
          </div>
        </div>
      </div>

      <div className="page-content fade-in">
        {data.has_filters && (
          <div style={{ padding: '10px 14px', background: 'var(--warning-bg)', border: '1px solid var(--warning)', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.85rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter size={14} /> Showing {data.filter_count} of {data.total_count} transactions
          </div>
        )}

        <div className="card">
          {data.transactions.length === 0 ? (
            <EmptyState
              icon={ArrowLeftRight}
              title="No transactions"
              description="Add a transaction to get started"
            />
          ) : (
            <div className="transaction-list">
              {data.transactions.map((tx) => (
                <div key={tx.id} className="transaction-row">
                  <div className="transaction-info">
                    <div className="transaction-category">
                      {tx.is_transfer && <ArrowLeftRight size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4, color: 'var(--transfer)' }} />}
                      {tx.category}
                      {tx.is_transfer && tx.from_wallet && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 8 }}>
                          {tx.from_wallet} → {tx.to_wallet}
                        </span>
                      )}
                    </div>
                    {tx.description && <div className="transaction-desc">{tx.description}</div>}
                  </div>
                  <div className={`transaction-amount ${tx.is_transfer ? 'transfer' : tx.transaction_type}`}>
                    {tx.sign}{formatAmount(tx.amount, '')}
                  </div>
                  <div className="transaction-date">{tx.date.split(' ')[0]}</div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {!tx.is_transfer && (
                      <>
                        <button className="btn-icon" onClick={() => setEditTx(tx)}><Edit3 size={14} /></button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)}><Trash2 size={14} /></button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showAddTx && (
        <Modal title="Add Transaction" onClose={() => setShowAddTx(false)}>
          <TransactionForm onSubmit={handleAdd} onCancel={() => setShowAddTx(false)} />
        </Modal>
      )}

      {editTx && (
        <Modal title="Edit Transaction" onClose={() => setEditTx(null)}>
          <TransactionForm isEdit={true} type={editTx.transaction_type} initial={editTx} onSubmit={handleEdit} onCancel={() => setEditTx(null)} />
        </Modal>
      )}

      {deleteTx && (
        <ConfirmDialog title="Delete Transaction" message={`Delete ${deleteTx.category} (${formatAmount(deleteTx.amount, '')})?`} onConfirm={handleDelete} onCancel={() => setDeleteTx(null)} danger />
      )}

      {showTransfer && transferCtx && (() => {
        const selectedTarget = transferCtx.target_wallets.find((w) => w.name === transferData.to_wallet)
        const targetCurrency = selectedTarget?.currency || ''
        const isCrossCurrency = targetCurrency && transferCtx.currency && targetCurrency !== transferCtx.currency
        return (
          <Modal title="Transfer" onClose={() => setShowTransfer(false)}>
            <form onSubmit={handleTransfer}>
              <div style={{ padding: '10px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.85rem' }}>
                From: <strong>{transferCtx.current_wallet}</strong> ({transferCtx.currency})
              </div>
              <div className="form-group">
                <label>To Wallet</label>
                <select className="form-input" value={transferData.to_wallet} onChange={(e) => setTransferData({ ...transferData, to_wallet: e.target.value, received_amount: '' })} required>
                  <option value="">Select wallet</option>
                  {transferCtx.target_wallets.map((w) => (
                    <option key={w.name} value={w.name}>{w.name} ({w.currency})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Amount ({transferCtx.currency})</label>
                <input type="number" step="0.01" min="0" className="form-input" value={transferData.amount} onChange={(e) => setTransferData({ ...transferData, amount: e.target.value })} required />
              </div>
              {isCrossCurrency && (
                <div className="form-group">
                  <label>Received Amount ({targetCurrency})</label>
                  <input type="number" step="0.01" min="0" className="form-input" value={transferData.received_amount} onChange={(e) => setTransferData({ ...transferData, received_amount: e.target.value })} placeholder={`Amount in ${targetCurrency}`} />
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowTransfer(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={transferLoading}>{transferLoading ? 'Sending...' : 'Transfer'}</button>
              </div>
            </form>
          </Modal>
        )
      })()}
    </>
  )
}
