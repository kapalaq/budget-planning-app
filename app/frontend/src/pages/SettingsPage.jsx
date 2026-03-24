import { useState, useEffect } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import { Settings, Globe, Clock } from 'lucide-react'

const LANGUAGES = {
  'en-US': 'English',
  'ru-RU': 'Russian',
  'kk-KZ': 'Kazakh',
}

const TIMEZONES = Array.from({ length: 27 }, (_, i) => i - 12)

export default function SettingsPage() {
  const [language, setLanguage] = useState('en-US')
  const [timezone, setTimezone] = useState(0)
  const [loading, setLoading] = useState(true)
  const { toasts, success, error: showError } = useToast()

  useEffect(() => {
    Promise.all([api.getLanguage(), api.getTimezone()])
      .then(([langRes, tzRes]) => {
        setLanguage(langRes.data?.language || 'en-US')
        setTimezone(tzRes.data?.timezone ?? 0)
      })
      .catch((err) => showError(err.message))
      .finally(() => setLoading(false))
  }, [showError])

  const handleLanguageChange = async (lang) => {
    try {
      await api.setLanguage(lang)
      setLanguage(lang)
      success(`Language changed to ${LANGUAGES[lang] || lang}`)
    } catch (err) { showError(err.message) }
  }

  const handleTimezoneChange = async (tz) => {
    try {
      const offset = parseInt(tz)
      await api.setTimezone(offset)
      setTimezone(offset)
      const sign = offset >= 0 ? '+' : ''
      success(`Timezone changed to GMT${sign}${offset}`)
    } catch (err) { showError(err.message) }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header"><h2>Settings</h2></div>
      <div className="page-content fade-in">
        <div style={{ maxWidth: 500, display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <Globe size={20} style={{ color: 'var(--accent)' }} />
              <div className="card-title" style={{ margin: 0 }}>Language</div>
            </div>
            <select
              className="form-input"
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
            >
              {Object.entries(LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>{name}</option>
              ))}
            </select>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <Clock size={20} style={{ color: 'var(--accent)' }} />
              <div className="card-title" style={{ margin: 0 }}>Timezone</div>
            </div>
            <select
              className="form-input"
              value={timezone}
              onChange={(e) => handleTimezoneChange(e.target.value)}
            >
              {TIMEZONES.map((tz) => {
                const sign = tz >= 0 ? '+' : ''
                return <option key={tz} value={tz}>GMT{sign}{tz}</option>
              })}
            </select>
          </div>
        </div>
      </div>
    </>
  )
}
