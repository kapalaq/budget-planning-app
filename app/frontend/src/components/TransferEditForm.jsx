import { useState, useEffect } from 'react'
import api from '../api/client'
import AmountInput from './AmountInput'
import t from '../i18n'

export default function TransferEditForm({ initial = {}, onSubmit, onCancel }) {
  const formatDateForInput = (dateStr) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr.replace(' ', 'T'))
      if (isNaN(d)) return ''
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch { return '' }
  }

  const [wallets, setWallets] = useState([])
  const [fromWallet, setFromWallet] = useState(initial.from_wallet || '')
  const [toWallet, setToWallet] = useState(initial.to_wallet || '')
  const [amount, setAmount] = useState(initial.amount || '')
  const [description, setDescription] = useState(initial.description || '')
  const [date, setDate] = useState(formatDateForInput(initial.date))
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.getWallets()
      .then((res) => {
        if (res.data?.wallets) setWallets(res.data.wallets)
      })
      .catch(() => {})
  }, [])

  const walletsChanged = fromWallet !== initial.from_wallet || toWallet !== initial.to_wallet

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!amount || !fromWallet || !toWallet) return
    setLoading(true)
    try {
      const payload = {
        amount: parseFloat(amount),
        description,
        from_wallet: fromWallet,
        to_wallet: toWallet,
        wallets_changed: walletsChanged,
      }
      if (date) {
        payload.date = date.replace('T', ' ') + ':00'
      }
      await onSubmit(payload)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {walletsChanged && (
        <div style={{ padding: '8px 12px', background: 'var(--bg-warning, rgba(255,180,0,0.1))', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.8rem', color: 'var(--text-warning, #e0a000)' }}>
          {t('transaction.transfer_note')}
        </div>
      )}

      <div className="form-group">
        <label>{t('transaction.transfer_from_wallet')}</label>
        <select
          className="form-input"
          value={fromWallet}
          onChange={(e) => {
            setFromWallet(e.target.value)
            if (e.target.value === toWallet) setToWallet('')
          }}
          required
        >
          <option value="">{t('transaction.transfer_from_wallet')}</option>
          {wallets.filter((w) => w.name !== toWallet).map((w) => (
            <option key={w.name} value={w.name}>{w.name} ({w.currency})</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>{t('transaction.transfer_to_wallet')}</label>
        <select
          className="form-input"
          value={toWallet}
          onChange={(e) => setToWallet(e.target.value)}
          required
        >
          <option value="">{t('transaction.transfer_to_wallet')}</option>
          {wallets.filter((w) => w.name !== fromWallet).map((w) => (
            <option key={w.name} value={w.name}>{w.name} ({w.currency})</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>{t('transaction.transfer_amount')}</label>
        <AmountInput
          value={amount}
          onChange={setAmount}
          autoFocus
          required
        />
      </div>

      <div className="form-group">
        <label>Date & Time</label>
        <input
          type="datetime-local"
          className="form-input"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>{t('transaction.transfer_description')}</label>
        <input
          type="text"
          className="form-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add a note..."
        />
      </div>

      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>{t('transaction.transfer_cancel')}</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? t('transaction.transfer_saving') : t('transaction.transfer_save')}
        </button>
      </div>
    </form>
  )
}
