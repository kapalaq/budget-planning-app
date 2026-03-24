import { useState, useEffect } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'
import { Settings, Globe, Clock, MessageCircle, Copy, ExternalLink } from 'lucide-react'

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
  const [linkCode, setLinkCode] = useState(null)
  const [deepLink, setDeepLink] = useState('')
  const [linkLoading, setLinkLoading] = useState(false)
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

  const handleGenerateLink = async () => {
    setLinkLoading(true)
    try {
      const res = await api.generateLinkCode()
      setLinkCode(res.code)
      setDeepLink(res.deep_link || '')
      success('Link code generated — expires in 5 minutes')
    } catch (err) { showError(err.message) }
    finally { setLinkLoading(false) }
  }

  const handleCopyCode = () => {
    navigator.clipboard.writeText(linkCode)
    success('Code copied to clipboard')
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
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <MessageCircle size={20} style={{ color: 'var(--accent)' }} />
              <div className="card-title" style={{ margin: 0 }}>Link Telegram</div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
              Connect your Telegram account to access your budget from the Telegram bot.
            </p>
            {!linkCode ? (
              <button className="btn btn-primary" onClick={handleGenerateLink} disabled={linkLoading}>
                {linkLoading ? 'Generating...' : 'Generate Link Code'}
              </button>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <code style={{
                    padding: '8px 12px', background: 'var(--bg-tertiary)',
                    borderRadius: 6, fontSize: 16, letterSpacing: 2, flex: 1, textAlign: 'center'
                  }}>{linkCode}</code>
                  <button className="btn" onClick={handleCopyCode} title="Copy code">
                    <Copy size={16} />
                  </button>
                </div>
                {deepLink && (
                  <a href={deepLink} target="_blank" rel="noopener noreferrer"
                    className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, textDecoration: 'none' }}>
                    <ExternalLink size={16} /> Open in Telegram
                  </a>
                )}
                <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: 0 }}>
                  {deepLink ? 'Click the button above or send' : 'Send'} <code>/start {linkCode}</code> to the bot. Expires in 5 minutes.
                </p>
                <button className="btn" onClick={handleGenerateLink} disabled={linkLoading} style={{ fontSize: 13 }}>
                  Generate new code
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
