import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import TransactionForm from '../components/TransactionForm'
import TransferEditForm from '../components/TransferEditForm'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ConfirmDialog'
import { useNavigate } from 'react-router-dom'
import {
  TrendingUp, TrendingDown, DollarSign, Plus, Trash2, Edit3,
  ArrowLeftRight, LayoutDashboard, Eye, EyeOff,
} from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
} from 'recharts'

const EXPENSE_COLORS = ['#e06c75', '#d19a66', '#c678dd', '#e5c07b', '#56b6c2', '#61afef', '#be5046', '#98c379', '#c7a035', '#5a8dc7']
const INCOME_COLORS = ['#56b6c2', '#61afef', '#98c379', '#c678dd', '#d19a66', '#e5c07b', '#5cb870', '#5a8dc7', '#6fcfb8', '#8b6fcf']

function assignCategoryColors(categories, palette, existingMap) {
  const colorMap = { ...existingMap }
  const usedColors = new Set(Object.values(colorMap))
  for (const name of categories) {
    if (!colorMap[name]) {
      const available = palette.find(c => !usedColors.has(c))
      colorMap[name] = available || palette[Object.keys(colorMap).length % palette.length]
      usedColors.add(colorMap[name])
    }
  }
  return colorMap
}

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTx, setShowAddTx] = useState(false)
  const [editTx, setEditTx] = useState(null)
  const [deleteTx, setDeleteTx] = useState(null)
  const [hiddenCategories, setHiddenCategories] = useState({ expense: [], income: [] })
  const [categoryColors, setCategoryColors] = useState({ expense: {}, income: {} })
  const { toasts, success, error: showError } = useToast()
  const navigate = useNavigate()

  const loadDashboard = useCallback(async () => {
    try {
      await api.processRecurring()
      const res = await api.getDashboard()
      setData(res.data)
    } catch (err) {
      showError(err.message)
    } finally {
      setLoading(false)
    }
  }, [showError])

  useEffect(() => { loadDashboard() }, [loadDashboard])

  const savedColorsRef = useRef(categoryColors)
  useEffect(() => { savedColorsRef.current = categoryColors }, [categoryColors])

  useEffect(() => {
    api.getHiddenChartCategories().then(res => {
      setHiddenCategories({ expense: [], income: [], ...res.data })
    }).catch(() => {})
    api.getCategoryColors().then(res => {
      setCategoryColors({ expense: {}, income: {}, ...res.data })
    }).catch(() => {})
  }, [])

  const toggleCategory = async (type, category) => {
    const current = hiddenCategories[type] || []
    const updated = current.includes(category)
      ? current.filter(c => c !== category)
      : [...current, category]
    const next = { ...hiddenCategories, [type]: updated }
    setHiddenCategories(next)
    try {
      await api.setHiddenChartCategories(next)
    } catch (err) {
      showError(err.message)
    }
  }

  const handleAddTransaction = async (txData) => {
    try {
      await api.addTransaction(txData)
      success('Transaction added')
      setShowAddTx(false)
      loadDashboard()
    } catch (err) {
      showError(err.message)
    }
  }

  const handleEditTransaction = async (txData) => {
    try {
      const txList = data.transactions
      const foundIdx = txList.findIndex((t) => t.id === editTx.id)
      if (foundIdx === -1) return
      const idx = foundIdx + 1
      await api.editTransaction(idx, txData)
      success('Transaction updated')
      setEditTx(null)
      loadDashboard()
    } catch (err) {
      showError(err.message)
    }
  }

  const handleEditTransfer = async (txData) => {
    try {
      const txList = data.transactions
      const foundIdx = txList.findIndex((t) => t.id === editTx.id)
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
    } catch (err) {
      showError(err.message)
    } finally {
      setEditTx(null)
      loadDashboard()
    }
  }

  const handleDeleteTransaction = async () => {
    try {
      const txList = data.transactions
      const foundIdx = txList.findIndex((t) => t.id === deleteTx.id)
      if (foundIdx === -1) return
      const idx = foundIdx + 1
      await api.deleteTransaction(idx)
      success('Transaction deleted')
      setDeleteTx(null)
      loadDashboard()
    } catch (err) {
      showError(err.message)
    }
  }

  if (loading) {
    return <div className="loading-page"><div className="spinner" /></div>
  }

  if (!data) return null

  const allExpenseData = Object.entries(data.expense_by_category || {}).map(([name, value]) => ({ name, value }))
  const allIncomeData = Object.entries(data.income_by_category || {}).map(([name, value]) => ({ name, value }))
  const expenseChartData = allExpenseData.filter(d => !(hiddenCategories.expense || []).includes(d.name))
  const incomeChartData = allIncomeData.filter(d => !(hiddenCategories.income || []).includes(d.name))

  const expenseColorMap = assignCategoryColors(allExpenseData.map(d => d.name), EXPENSE_COLORS, categoryColors.expense || {})
  const incomeColorMap = assignCategoryColors(allIncomeData.map(d => d.name), INCOME_COLORS, categoryColors.income || {})

  const hasNewExpenseColors = Object.keys(expenseColorMap).length > Object.keys(categoryColors.expense || {}).length
  const hasNewIncomeColors = Object.keys(incomeColorMap).length > Object.keys(categoryColors.income || {}).length
  if (hasNewExpenseColors || hasNewIncomeColors) {
    const updated = { expense: expenseColorMap, income: incomeColorMap }
    if (JSON.stringify(updated) !== JSON.stringify(savedColorsRef.current)) {
      savedColorsRef.current = updated
      setCategoryColors(updated)
      api.setCategoryColors(updated).catch(() => {})
    }
  }

  return (
    <>
      <ToastContainer toasts={toasts} />

      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>{data.wallet_name}</h2>
            <p>{data.currency} wallet</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowAddTx(true)}>
            <Plus size={18} /> Add Transaction
          </button>
        </div>
      </div>

      <div className="page-content fade-in">
        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="label"><DollarSign size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Balance</div>
            <div className="value">{formatAmount(data.balance, data.currency)}</div>
          </div>
          <div className="stat-card">
            <div className="label"><TrendingUp size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Income</div>
            <div className="value income">{formatAmount(data.total_income, data.currency)}</div>
          </div>
          <div className="stat-card">
            <div className="label"><TrendingDown size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Expenses</div>
            <div className="value expense">{formatAmount(data.total_expense, data.currency)}</div>
          </div>
        </div>

        {/* Charts */}
        {(allExpenseData.length > 0 || allIncomeData.length > 0) && (
          <div className="two-col" style={{ marginBottom: 24 }}>
            {allExpenseData.length > 0 && (
              <div className="card">
                <div className="card-title">Expenses by Category</div>
                <div className="chart-container" style={{ height: 250 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={expenseChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {expenseChartData.map((entry) => (
                          <Cell key={entry.name} fill={expenseColorMap[entry.name] || EXPENSE_COLORS[0]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border)',
                          borderRadius: 8,
                          color: 'var(--text-primary)',
                        }}
                        formatter={(value) => formatAmount(value, data.currency)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                  {allExpenseData.map((item) => {
                    const hidden = (hiddenCategories.expense || []).includes(item.name)
                    return (
                      <button
                        key={item.name}
                        onClick={() => toggleCategory('expense', item.name)}
                        style={{
                          fontSize: '0.75rem',
                          color: hidden ? 'var(--text-muted)' : 'var(--text-secondary)',
                          display: 'flex', alignItems: 'center', gap: 4,
                          background: 'none', border: 'none', cursor: 'pointer',
                          opacity: hidden ? 0.45 : 1, padding: '2px 4px', borderRadius: 4,
                          textDecoration: hidden ? 'line-through' : 'none',
                        }}
                        title={hidden ? 'Show in chart' : 'Hide from chart'}
                      >
                        <span style={{ width: 8, height: 8, borderRadius: 2, background: expenseColorMap[item.name] || EXPENSE_COLORS[0], display: 'inline-block' }} />
                        {item.name}
                        {hidden ? <EyeOff size={10} /> : <Eye size={10} />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
            {allIncomeData.length > 0 && (
              <div className="card">
                <div className="card-title">Income by Category</div>
                <div className="chart-container" style={{ height: 250 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={incomeChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {incomeChartData.map((entry) => (
                          <Cell key={entry.name} fill={incomeColorMap[entry.name] || INCOME_COLORS[0]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border)',
                          borderRadius: 8,
                          color: 'var(--text-primary)',
                        }}
                        formatter={(value) => formatAmount(value, data.currency)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                  {allIncomeData.map((item) => {
                    const hidden = (hiddenCategories.income || []).includes(item.name)
                    return (
                      <button
                        key={item.name}
                        onClick={() => toggleCategory('income', item.name)}
                        style={{
                          fontSize: '0.75rem',
                          color: hidden ? 'var(--text-muted)' : 'var(--text-secondary)',
                          display: 'flex', alignItems: 'center', gap: 4,
                          background: 'none', border: 'none', cursor: 'pointer',
                          opacity: hidden ? 0.45 : 1, padding: '2px 4px', borderRadius: 4,
                          textDecoration: hidden ? 'line-through' : 'none',
                        }}
                        title={hidden ? 'Show in chart' : 'Hide from chart'}
                      >
                        <span style={{ width: 8, height: 8, borderRadius: 2, background: incomeColorMap[item.name] || INCOME_COLORS[0], display: 'inline-block' }} />
                        {item.name}
                        {hidden ? <EyeOff size={10} /> : <Eye size={10} />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Goals and Bills summaries */}
        {(data.active_goals?.length > 0 || data.active_bills?.length > 0) && (
          <div className="two-col" style={{ marginBottom: 24 }}>

            {/* Left Goals Block */}
            {data.active_bills?.length > 0 && (
              <div className="card">
                <div className="card-title">Active Bills</div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: 12,
                    marginTop: 12,
                  }}
                >
                  {data.active_bills.map((g) => (
                    <div
                      key={g.name}
                      onClick={() => navigate('/bills')}
                      style={{
                        padding: 12,
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>
                        {g.name}
                      </div>
                      <div className="progress-bar" style={{ marginBottom: 6 }}>
                        <div
                          className="fill"
                          style={{ width: `${Math.min(g.progress, 100)}%` }}
                        />
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {formatAmount(g.saved, g.currency)} / {formatAmount(g.target, g.currency)} ({g.progress.toFixed(0)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Right Goals Block */}
            {data.active_goals?.length > 0 && (
              <div className="card">
                <div className="card-title">Active Goals</div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: 12,
                    marginTop: 12,
                  }}
                >
                  {data.active_goals.map((g) => (
                    <div
                      key={`${g.name}-duplicate`}
                      onClick={() => navigate('/goals')}
                      style={{
                        padding: 12,
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>
                        {g.name}
                      </div>
                      <div className="progress-bar" style={{ marginBottom: 6 }}>
                        <div
                          className="fill"
                          style={{ width: `${Math.min(g.progress, 100)}%` }}
                        />
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {formatAmount(g.saved, g.currency)} / {formatAmount(g.target, g.currency)} ({g.progress.toFixed(0)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

        {/* Transactions */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              Recent Transactions
              {data.has_filters && <span style={{ marginLeft: 8, fontSize: '0.75rem', color: 'var(--warning)' }}>(filtered)</span>}
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {data.transactions.length} transaction{data.transactions.length !== 1 ? 's' : ''}
            </span>
          </div>

          {data.transactions.length === 0 ? (
            <EmptyState
              icon={LayoutDashboard}
              title="No transactions yet"
              description="Add your first transaction to get started"
            />
          ) : (
            <div className="transaction-list">
              {data.transactions.map((tx) => (
                <div key={tx.id} className="transaction-row">
                  <div className="transaction-info">
                    <div className="transaction-category">
                      {tx.is_transfer && <ArrowLeftRight size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4, color: 'var(--transfer)' }} />}
                      {tx.category}
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
                        <button className="btn-icon" onClick={() => setEditTx(tx)} title="Edit">
                          <Edit3 size={14} />
                        </button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)} title="Delete">
                          <Trash2 size={14} />
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="btn-icon" onClick={() => setEditTx(tx)} title="Edit Transfer">
                          <Edit3 size={14} />
                        </button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)} title="Delete Transfer">
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add modal */}
      {showAddTx && (
        <Modal title="Add Transaction" onClose={() => setShowAddTx(false)}>
          <TransactionForm onSubmit={handleAddTransaction} onCancel={() => setShowAddTx(false)} />
        </Modal>
      )}

      {/* Edit modal */}
      {editTx && !editTx.is_transfer && (
        <Modal title="Edit Transaction" onClose={() => setEditTx(null)}>
          <TransactionForm
            type={editTx.transaction_type}
            initial={editTx}
            onSubmit={handleEditTransaction}
            onCancel={() => setEditTx(null)}
            isEdit={true}
          />
        </Modal>
      )}

      {editTx && editTx.is_transfer && (
        <Modal title="Edit Transfer" onClose={() => setEditTx(null)}>
          <TransferEditForm
            initial={editTx}
            onSubmit={handleEditTransfer}
            onCancel={() => setEditTx(null)}
          />
        </Modal>
      )}

      {/* Delete confirm */}
      {deleteTx && (
        <ConfirmDialog
          title="Delete Transaction"
          message={`Delete ${deleteTx.category} transaction of ${formatAmount(deleteTx.amount, '')}?`}
          onConfirm={handleDeleteTransaction}
          onCancel={() => setDeleteTx(null)}
          danger
        />
      )}
    </>
  )
}
