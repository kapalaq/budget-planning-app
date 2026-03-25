import { useState } from 'react'

function evaluate(expr) {
  try {
    const sanitized = expr.replace(/[^0-9+\-*/.() ]/g, '')
    if (!sanitized) return ''
    const result = Function('"use strict"; return (' + sanitized + ')')()
    if (typeof result !== 'number' || !isFinite(result)) return 'Error'
    return Math.round(result * 100) / 100
  } catch {
    return 'Error'
  }
}

export default function Calculator({ value, onChange, onClose }) {
  const [expression, setExpression] = useState(value ? String(value) : '')
  const [justEvaluated, setJustEvaluated] = useState(false)

  const result = evaluate(expression)
  const hasOperator = /[+\-*/]/.test(expression.replace(/^-/, ''))

  const handleButton = (btn) => {
    if (btn === 'AC') {
      setExpression('')
      setJustEvaluated(false)
      onChange('')
      return
    }

    if (btn === '⌫') {
      setExpression((prev) => prev.slice(0, -1))
      setJustEvaluated(false)
      return
    }

    if (btn === '±') {
      setExpression((prev) => {
        if (!prev) return '-'
        if (prev.startsWith('-')) return prev.slice(1)
        return '-' + prev
      })
      return
    }

    if (btn === '%') {
      if (expression && result !== 'Error') {
        const percentVal = String(Math.round((result / 100) * 100) / 100)
        setExpression(percentVal)
        onChange(percentVal)
        setJustEvaluated(true)
      }
      return
    }

    if (btn === '=') {
      if (result !== 'Error' && result !== '') {
        const val = String(result)
        setExpression(val)
        onChange(val)
        setJustEvaluated(true)
      }
      return
    }

    const isOperator = ['+', '−', '×', '÷'].includes(btn)
    const opMap = { '×': '*', '÷': '/', '−': '-' }
    const char = opMap[btn] || btn

    if (isOperator) {
      if (justEvaluated) {
        setJustEvaluated(false)
      }
      setExpression((prev) => {
        if (!prev && char !== '-') return prev
        const last = prev[prev.length - 1]
        if (['+', '-', '*', '/'].includes(last)) {
          return prev.slice(0, -1) + char
        }
        return prev + char
      })
      return
    }

    // Digit or dot
    if (justEvaluated) {
      setExpression(char)
      setJustEvaluated(false)
      return
    }

    setExpression((prev) => prev + char)
  }

  const buttons = [
    ['AC', '±', '%', '÷'],
    ['7', '8', '9', '×'],
    ['4', '5', '6', '−'],
    ['1', '2', '3', '+'],
    ['0', '.', '⌫', '='],
  ]

  const getButtonClass = (btn) => {
    if (btn === '÷' || btn === '×' || btn === '−' || btn === '+' || btn === '=') return 'calc-btn calc-btn-op'
    if (btn === 'AC' || btn === '±' || btn === '%' || btn === '⌫') return 'calc-btn calc-btn-fn'
    return 'calc-btn'
  }

  return (
    <>
      <div className="calc-display">
        <div className="calc-expression">{expression || '0'}</div>
        {hasOperator && result !== 'Error' && result !== '' && (
          <div className="calc-result">= {result}</div>
        )}
        {result === 'Error' && <div className="calc-result calc-error">Error</div>}
      </div>
      <div className="calc-grid">
        {buttons.flat().map((btn, i) => (
          <button
            key={i}
            type="button"
            className={getButtonClass(btn)}
            onClick={() => handleButton(btn)}
          >
            {btn}
          </button>
        ))}
      </div>
      <button type="button" className="calc-apply" onClick={() => {
        if (result !== 'Error' && result !== '') {
          onChange(String(result))
          onClose?.()
        }
      }}>
        Apply Result
      </button>
    </>
  )
}
