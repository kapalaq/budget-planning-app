import { useState, useEffect } from 'react'
import api from '../api/client'

export default function TransactionForm({ 
  type = 'expense', 
  initial = {}, 
  onSubmit, 
  onCancel, 
  isEdit = false
}) {
  const [amount, setAmount] = useState(initial.amount || '')
  const [category, setCategory] = useState(initial.category || '')
  const [description, setDescription] = useState(initial.description || '')
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
      await onSubmit({
        amount: parseFloat(amount),
        category,
        description,
        transaction_type: txType === 'income' ? '+' : '-',
      })
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
          onClick={() => setTxType('expense')}
        >
          Expense
        </button>
        <button
          type="button"
          disabled={isEdit}
          className={`type-tab ${txType === 'income' ? 'active' : ''}`}
          onClick={() => setTxType('income')}
        >
          Income
        </button>
      </div>

      <div className="form-group">
        <label>Amount</label>
        <input
          type="number"
          step="0.01"
          min="0"
          className="form-input"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
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