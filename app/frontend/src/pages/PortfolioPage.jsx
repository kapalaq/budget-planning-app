import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import EmptyState from '../components/EmptyState'
import { PieChart as PieChartIcon } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const COLORS = ['#56b6c2', '#61afef', '#98c379', '#c678dd', '#d19a66', '#e5c07b', '#5cb870', '#e06c75', '#5a8dc7', '#6fcfb8']

function formatAmount(amount, currency) {
  return `${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || ''}`
}

export default function PortfolioPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toasts, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = await api.getPortfolio()
      setData(res.data)
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="loading-page"><div className="spinner" /></div>
  if (!data) return null

  const chartData = (data.wallets || []).map((w) => ({
    name: `${w.name} (${w.currency})`,
    value: w.converted,
  })).filter((d) => d.value > 0)

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header"><h2>Portfolio</h2></div>
      <div className="page-content fade-in">
        <div className="stats-grid" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="label">Total Balance</div>
            <div className="value">{formatAmount(data.total_balance, data.base_currency)}</div>
          </div>
          <div className="stat-card">
            <div className="label">Wallets</div>
            <div className="value">{data.wallets?.length || 0}</div>
          </div>
          <div className="stat-card">
            <div className="label">Base Currency</div>
            <div className="value">{data.base_currency}</div>
          </div>
        </div>

        {!data.rates_available && (
          <div style={{ padding: '10px 14px', background: 'var(--warning-bg)', border: '1px solid var(--warning)', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.85rem', color: 'var(--warning)' }}>
            Some exchange rates are unavailable. Amounts may be approximate.
          </div>
        )}

        {chartData.length > 0 && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-title">Balance Distribution</div>
            <div className="chart-container" style={{ height: 280 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={chartData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value">
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
                    formatter={(value) => formatAmount(value, data.base_currency)}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              {chartData.map((item, i) => (
                <span key={item.name} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length], display: 'inline-block' }} />
                  {item.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {(data.wallets || []).length === 0 ? (
          <EmptyState icon={PieChartIcon} title="No wallets" description="Create a wallet to see your portfolio" />
        ) : (
          <div className="card">
            <div className="card-title">Wallet Breakdown</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 12 }}>
              {data.wallets.map((w, i) => (
                <div key={w.name} className="transaction-row">
                  <div className="transaction-info">
                    <div className="transaction-category">
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length], display: 'inline-block', marginRight: 8 }} />
                      {w.name}
                    </div>
                    <div className="transaction-desc">{w.currency}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{formatAmount(w.balance, w.currency)}</div>
                    {w.currency !== data.base_currency && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{formatAmount(w.converted, data.base_currency)}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
