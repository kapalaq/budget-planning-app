import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import TransactionForm from '../components/TransactionForm'
import TransferEditForm from '../components/TransferEditForm'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ConfirmDialog'
import AmountInput from '../components/AmountInput'
import {
  Plus, Trash2, Edit3, ArrowLeftRight, Send, Filter, X, ArrowUpDown, Search,
} from 'lucide-react'

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

const DATE_FILTERS = [
  { value: 'today', label: 'Today' },
  { value: 'last_week', label: 'Last Week' },
  { value: 'last_month', label: 'Last Month' },
  { value: 'this_month', label: 'This Month' },
  { value: 'last_year', label: 'Last Year' },
  { value: 'this_year', label: 'This Year' },
]

const TYPE_FILTERS = [
  { value: 'income_only', label: 'Income Only' },
  { value: 'expense_only', label: 'Expense Only' },
  { value: 'transfers_only', label: 'Transfers Only' },
  { value: 'no_transfers', label: 'No Transfers' },
  { value: 'recurring_only', label: 'Recurring Only' },
  { value: 'non_recurring', label: 'Non-Recurring Only' },
]

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
  const [showFilterModal, setShowFilterModal] = useState(false)
  const [showSortModal, setShowSortModal] = useState(false)
  const [sortOptions, setSortOptions] = useState(null)
  const [activeFilters, setActiveFilters] = useState([])
  const [filterForm, setFilterForm] = useState({ filter_type: '', start_date: '', end_date: '', min_amount: '', max_amount: '', search_term: '', categories: '' })
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

  const handleEditTransfer = async (txData) => {
    try {
      const foundIdx = data.transactions.findIndex((t) => t.id === editTx.id)
      if (foundIdx === -1) return
      const idx = foundIdx + 1
      if (txData.wallets_changed) {
        const currentWallet = data.wallet_name
        await api.deleteTransaction(idx)
        await api.switchWallet(txData.from_wallet)
        await api.transfer({
          target_wallet_name: txData.to_wallet,
          amount: txData.amount,
          description: txData.description,
        })
        if (currentWallet) await api.switchWallet(currentWallet)
        success('Transfer updated')
      } else {
        await api.editTransaction(idx, { amount: txData.amount, description: txData.description })
        success('Transfer updated')
      }
    } catch (err) { showError(err.message) }
    finally {
      setEditTx(null)
      load()
    }
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

  const openFilterModal = async () => {
    try {
      const res = await api.getActiveFilters()
      setActiveFilters(res.data?.filters || [])
    } catch { /* ignore */ }
    setFilterForm({ filter_type: '', start_date: '', end_date: '', min_amount: '', max_amount: '', search_term: '', categories: '' })
    setShowFilterModal(true)
  }

  const handleAddFilter = async (e) => {
    e.preventDefault()
    const ft = filterForm.filter_type
    if (!ft) return
    const payload = { filter_type: ft }
    if (ft === 'date_range') {
      if (filterForm.start_date) payload.start_date = filterForm.start_date
      if (filterForm.end_date) payload.end_date = filterForm.end_date
    } else if (ft === 'amount_range') {
      if (filterForm.min_amount) payload.min_amount = parseFloat(filterForm.min_amount)
      if (filterForm.max_amount) payload.max_amount = parseFloat(filterForm.max_amount)
    } else if (ft === 'description') {
      payload.search_term = filterForm.search_term
    } else if (ft === 'category') {
      payload.categories = filterForm.categories.split(',').map(c => c.trim()).filter(Boolean)
      payload.mode = 'include'
    }
    try {
      await api.addFilter(payload)
      success('Filter added')
      const res = await api.getActiveFilters()
      setActiveFilters(res.data?.filters || [])
      setFilterForm({ filter_type: '', start_date: '', end_date: '', min_amount: '', max_amount: '', search_term: '', categories: '' })
      load()
    } catch (err) { showError(err.message) }
  }

  const handleRemoveFilter = async (index) => {
    try {
      await api.removeFilter(index)
      success('Filter removed')
      const res = await api.getActiveFilters()
      setActiveFilters(res.data?.filters || [])
      load()
    } catch (err) { showError(err.message) }
  }

  const openSortModal = async () => {
    try {
      const res = await api.getSortingOptions()
      setSortOptions(res.data?.options || {})
      setShowSortModal(true)
    } catch (err) { showError(err.message) }
  }

  const handleSetSorting = async (key) => {
    try {
      await api.setSorting({ strategy_key: key })
      success('Sorting updated')
      setShowSortModal(false)
      load()
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>
  if (!data) return null

  const needsExtra = ['date_range', 'amount_range', 'description', 'category'].includes(filterForm.filter_type)

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header">
        <div className="page-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Transactions</h2>
            <p>{data.wallet_name} - {data.currency}{data.sorting_strategy ? ` · Sorted: ${data.sorting_strategy}` : ''}</p>
          </div>
          <div className="page-header-actions" style={{ display: 'flex', gap: 8 }}>
            {data.has_filters && (
              <button className="btn btn-secondary btn-sm" onClick={handleClearFilters}>
                <X size={14} /> Clear
              </button>
            )}
            <button className="btn btn-secondary btn-sm" onClick={openFilterModal}>
              <Filter size={14} /> Filter
            </button>
            <button className="btn btn-secondary btn-sm" onClick={openSortModal}>
              <ArrowUpDown size={14} /> Sort
            </button>
            <button className="btn btn-secondary btn-sm" onClick={openTransfer}>
              <Send size={14} /> Transfer
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddTx(true)}>
              <Plus size={16} /> Add
            </button>
          </div>
        </div>
      </div>

      <div className="page-content fade-in">
        {data.has_filters && (
          <div style={{ padding: '10px 14px', background: 'var(--warning-bg)', border: '1px solid var(--warning)', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.85rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter size={14} /> Showing {data.filter_count} of {data.total_count} transactions
            {data.filter_summary && <span style={{ marginLeft: 8, opacity: 0.8 }}>({data.filter_summary})</span>}
          </div>
        )}

        <div className="card">
          {data.transactions.length === 0 ? (
            <EmptyState
              icon={ArrowLeftRight}
              title="No transactions"
              description={data.has_filters ? 'No transactions match your filters' : 'Add a transaction to get started'}
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
                    {!tx.is_transfer ? (
                      <>
                        <button className="btn-icon" onClick={() => setEditTx(tx)}><Edit3 size={14} /></button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)}><Trash2 size={14} /></button>
                      </>
                    ) : (
                      <>
                        <button className="btn-icon" onClick={() => setEditTx(tx)} title="Edit Transfer"><Edit3 size={14} /></button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)} title="Delete Transfer"><Trash2 size={14} /></button>
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

      {editTx && !editTx.is_transfer && (
        <Modal title="Edit Transaction" onClose={() => setEditTx(null)}>
          <TransactionForm isEdit={true} type={editTx.transaction_type} initial={editTx} onSubmit={handleEdit} onCancel={() => setEditTx(null)} />
        </Modal>
      )}

      {editTx && editTx.is_transfer && (
        <Modal title="Edit Transfer" onClose={() => setEditTx(null)}>
          <TransferEditForm initial={editTx} onSubmit={handleEditTransfer} onCancel={() => setEditTx(null)} />
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
                <AmountInput value={transferData.amount} onChange={(v) => setTransferData({ ...transferData, amount: v })} required />
              </div>
              {isCrossCurrency && (
                <div className="form-group">
                  <label>Received Amount ({targetCurrency})</label>
                  <AmountInput value={transferData.received_amount} onChange={(v) => setTransferData({ ...transferData, received_amount: v })} placeholder={`Amount in ${targetCurrency}`} />
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

      {showFilterModal && (
        <Modal title="Filters" onClose={() => setShowFilterModal(false)}>
          {activeFilters.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8, display: 'block' }}>Active Filters</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {activeFilters.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                    <span><strong>{f.name}</strong>: {f.description}</span>
                    <button className="btn-icon" onClick={() => handleRemoveFilter(i)} title="Remove filter"><X size={14} /></button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleAddFilter}>
            <div className="form-group">
              <label>Add Filter</label>
              <select className="form-input" value={filterForm.filter_type} onChange={(e) => setFilterForm({ ...filterForm, filter_type: e.target.value })}>
                <option value="">Select filter type...</option>
                <optgroup label="Date">
                  {DATE_FILTERS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                  <option value="date_range">Custom Date Range</option>
                </optgroup>
                <optgroup label="Type">
                  {TYPE_FILTERS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                </optgroup>
                <optgroup label="Amount">
                  <option value="large_transactions">Large Transactions (&gt;= 10000)</option>
                  <option value="small_transactions">Small Transactions (&lt;= 100)</option>
                  <option value="amount_range">Custom Amount Range</option>
                </optgroup>
                <optgroup label="Other">
                  <option value="description">By Description</option>
                  <option value="category">By Category</option>
                </optgroup>
              </select>
            </div>

            {filterForm.filter_type === 'date_range' && (
              <div style={{ display: 'flex', gap: 8 }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Start Date</label>
                  <input type="date" className="form-input" value={filterForm.start_date} onChange={(e) => setFilterForm({ ...filterForm, start_date: e.target.value })} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>End Date</label>
                  <input type="date" className="form-input" value={filterForm.end_date} onChange={(e) => setFilterForm({ ...filterForm, end_date: e.target.value })} />
                </div>
              </div>
            )}

            {filterForm.filter_type === 'amount_range' && (
              <div style={{ display: 'flex', gap: 8 }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Min Amount</label>
                  <input type="number" step="0.01" min="0" className="form-input" value={filterForm.min_amount} onChange={(e) => setFilterForm({ ...filterForm, min_amount: e.target.value })} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Max Amount</label>
                  <input type="number" step="0.01" min="0" className="form-input" value={filterForm.max_amount} onChange={(e) => setFilterForm({ ...filterForm, max_amount: e.target.value })} />
                </div>
              </div>
            )}

            {filterForm.filter_type === 'description' && (
              <div className="form-group">
                <label>Search Term</label>
                <div style={{ position: 'relative' }}>
                  <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input type="text" className="form-input" style={{ paddingLeft: 30 }} value={filterForm.search_term} onChange={(e) => setFilterForm({ ...filterForm, search_term: e.target.value })} placeholder="Search in description..." required />
                </div>
              </div>
            )}

            {filterForm.filter_type === 'category' && (
              <div className="form-group">
                <label>Categories (comma-separated)</label>
                <input type="text" className="form-input" value={filterForm.categories} onChange={(e) => setFilterForm({ ...filterForm, categories: e.target.value })} placeholder="Food, Transport, Salary" required />
              </div>
            )}

            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowFilterModal(false)}>Close</button>
              {activeFilters.length > 0 && (
                <button type="button" className="btn btn-secondary" onClick={async () => { await handleClearFilters(); setActiveFilters([]); }}>Clear All</button>
              )}
              <button type="submit" className="btn btn-primary" disabled={!filterForm.filter_type || (needsExtra && filterForm.filter_type === 'description' && !filterForm.search_term) || (needsExtra && filterForm.filter_type === 'category' && !filterForm.categories)}>
                <Plus size={14} /> Add Filter
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showSortModal && sortOptions && (
        <Modal title="Sort Transactions" onClose={() => setShowSortModal(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(sortOptions).map(([key, name]) => (
              <button
                key={key}
                className={`btn ${data.sorting_strategy === name ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => handleSetSorting(key)}
              >
                {data.sorting_strategy === name && <span style={{ marginRight: 6 }}>&#10003;</span>}
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
