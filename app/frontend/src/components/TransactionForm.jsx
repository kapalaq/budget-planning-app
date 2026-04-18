import { useState, useEffect } from 'react'
import api from '../api/client'
import AmountInput from './AmountInput'

export default function TransactionForm({ 
  type = 'expense', 
  initial = {}, 
  onSubmit, 
  onCancel, 
  isEdit = false
}) {
  const formatDateForInput = (dateStr) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr.replace(' ', 'T'))
      if (isNaN(d)) return ''
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch { return '' }
  }

  const [amount, setAmount] = useState(initial.amount || '')
  const [category, setCategory] = useState(initial.category || '')
  const [description, setDescription] = useState(initial.description || '')
  const [date, setDate] = useState(formatDateForInput(initial.date))
  const [categories, setCategories] = useState([])
  const [txType, setTxType] = useState(type)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.getCategories(txType)
      .then((res) => {
        if (res.data?.categories) setCategories(res.data.categories)
      })
      .catch(() => {})
  }, [txType])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!amount || !category) return
    setLoading(true)
    try {
      const payload = {
        amount: parseFloat(amount),
        category,
        description,
        transaction_type: txType === 'income' ? '+' : '-',
      }
      if (date) {
        const parts = date.replace('T', ' ')
        payload.date = parts.length <= 16 ? parts + ':00' : parts
      }
      await onSubmit(payload)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="type-tabs" style={{ marginBottom: 16 }}>
        <button
          type="button"
          disabled={isEdit}
          className={`type-tab ${txType === 'expense' ? 'active' : ''}`}
          onClick={() => { if (!isEdit) setTxType('expense') }}
        >
          Expense
        </button>
        <button
          type="button"
          disabled={isEdit}
          className={`type-tab ${txType === 'income' ? 'active' : ''}`}
          onClick={() => { if (!isEdit) setTxType('income') }}
        >
          Income
        </button>
      </div>

      <div className="form-group">
        <label>Amount</label>
        <AmountInput
          value={amount}
          onChange={setAmount}
          autoFocus
          required
        />
      </div>

      <div className="form-group">
        <label>Category</label>
        <select
          className="form-input"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          required
        >
          <option value="">Select category</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
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
        <label>Description (optional)</label>
        <input
          type="text"
          className="form-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add a note..."
        />
      </div>

      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  )
}