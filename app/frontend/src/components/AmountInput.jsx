import { useState, useRef, useEffect } from 'react'
import Calculator from './Calculator'
import { Calculator as CalcIcon } from 'lucide-react'

export default function AmountInput({ value, onChange, placeholder = '0.00', required = false, autoFocus = false, className = '' }) {
  const [showCalc, setShowCalc] = useState(false)
  const wrapperRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowCalc(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="amount-input-wrapper" ref={wrapperRef}>
      <div className="amount-input-row">
        <input
          type="number"
          step="0.01"
          min="0"
          className={`form-input amount-input-field ${className}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          autoFocus={autoFocus}
        />
        <button
          type="button"
          className={`calc-toggle ${showCalc ? 'active' : ''}`}
          onClick={() => setShowCalc(!showCalc)}
          title="Calculator"
        >
          <CalcIcon size={18} />
        </button>
      </div>
      {showCalc && (
        <Calculator
          value={value}
          onChange={onChange}
          onClose={() => setShowCalc(false)}
        />
      )}
    </div>
  )
}
