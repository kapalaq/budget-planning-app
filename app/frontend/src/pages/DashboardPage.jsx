import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import Modal from '../components/Modal'
import TransactionForm from '../components/TransactionForm'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ConfirmDialog'
import {
  TrendingUp, TrendingDown, DollarSign, Plus, Trash2, Edit3,
  ArrowLeftRight, LayoutDashboard,
} from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
} from 'recharts'

const COLORS = ['#5cb870', '#4a9e5c', '#3a7d49', '#2d6b3a', '#c7a035', '#5a8dc7', '#c75454', '#8b6fcf', '#cf6f8b', '#6fcfb8']

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddTx, setShowAddTx] = useState(false)
  const [editTx, setEditTx] = useState(null)
  const [deleteTx, setDeleteTx] = useState(null)
  const { toasts, success, error: showError } = useToast()

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
      const idx = txList.findIndex((t) => t.id === editTx.id) + 1
      if (idx === -1) return
      await api.editTransaction(idx, txData)
      success('Transaction updated')
      setEditTx(null)
      loadDashboard()
    } catch (err) {
      showError(err.message)
    }
  }

  const handleDeleteTransaction = async () => {
    try {
      const txList = data.transactions
      const idx = txList.findIndex((t) => t.id === deleteTx.id) + 1
      if (idx === -1) return
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

  const expenseChartData = Object.entries(data.expense_by_category || {}).map(([name, value]) => ({ name, value }))
  const incomeChartData = Object.entries(data.income_by_category || {}).map(([name, value]) => ({ name, value }))

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
        {(expenseChartData.length > 0 || incomeChartData.length > 0) && (
          <div className="two-col" style={{ marginBottom: 24 }}>
            {expenseChartData.length > 0 && (
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
                        {expenseChartData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
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
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                  {expenseChartData.map((item, i) => (
                    <span key={item.name} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length], display: 'inline-block' }} />
                      {item.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {incomeChartData.length > 0 && (
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
                        {incomeChartData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
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
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                  {incomeChartData.map((item, i) => (
                    <span key={item.name} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length], display: 'inline-block' }} />
                      {item.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Goals summary */}
        {data.active_goals?.length > 0 && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-title">Active Goals</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginTop: 12 }}>
              {data.active_goals.map((g) => (
                <div key={g.name} style={{ padding: 12, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>{g.name}</div>
                  <div className="progress-bar" style={{ marginBottom: 6 }}>
                    <div className="fill" style={{ width: `${Math.min(g.progress, 100)}%` }} />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {formatAmount(g.saved, g.currency)} / {formatAmount(g.target, g.currency)} ({g.progress.toFixed(0)}%)
                  </div>
                </div>
              ))}
            </div>
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
                    {!tx.is_transfer && (
                      <>
                        <button className="btn-icon" onClick={() => setEditTx(tx)} title="Edit">
                          <Edit3 size={14} />
                        </button>
                        <button className="btn-icon" onClick={() => setDeleteTx(tx)} title="Delete">
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
      {editTx && (
        <Modal title="Edit Transaction" onClose={() => setEditTx(null)}>
          <TransactionForm
            type={editTx.transaction_type}
            initial={editTx}
            onSubmit={handleEditTransaction}
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
