import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import Calculator from './Calculator'
import { Calculator as CalcIcon } from 'lucide-react'

export default function AmountInput({ value, onChange, placeholder = '0.00', required = false, autoFocus = false, className = '' }) {
  const [showCalc, setShowCalc] = useState(false)
  const [calcPos, setCalcPos] = useState({ top: 0, left: 0 })
  const toggleRef = useRef(null)
  const calcRef = useRef(null)

  const updatePosition = useCallback(() => {
    if (!toggleRef.current) return
    const rect = toggleRef.current.getBoundingClientRect()
    const calcWidth = 260
    let left = rect.right - calcWidth
    if (left < 8) left = 8
    if (left + calcWidth > window.innerWidth - 8) left = window.innerWidth - calcWidth - 8
    setCalcPos({ top: rect.bottom + 6, left })
  }, [])

  useEffect(() => {
    if (!showCalc) return
    updatePosition()
    window.addEventListener('scroll', updatePosition, true)
    window.addEventListener('resize', updatePosition)
    return () => {
      window.removeEventListener('scroll', updatePosition, true)
      window.removeEventListener('resize', updatePosition)
    }
  }, [showCalc, updatePosition])

  useEffect(() => {
    if (!showCalc) return
    const handleClickOutside = (e) => {
      if (
        toggleRef.current && !toggleRef.current.contains(e.target) &&
        calcRef.current && !calcRef.current.contains(e.target)
      ) {
        setShowCalc(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showCalc])

  return (
    <div className="amount-input-wrapper">
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
          ref={toggleRef}
          type="button"
          className={`calc-toggle ${showCalc ? 'active' : ''}`}
          onClick={() => setShowCalc(!showCalc)}
          title="Calculator"
        >
          <CalcIcon size={18} />
        </button>
      </div>
      {showCalc && createPortal(
        <div
          ref={calcRef}
          className="calculator"
          style={{ top: calcPos.top, left: calcPos.left }}
        >
          <Calculator
            value={value}
            onChange={onChange}
            onClose={() => setShowCalc(false)}
          />
        </div>,
        document.body
      )}
    </div>
  )
}
