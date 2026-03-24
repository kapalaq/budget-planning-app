import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TransactionsPage from './pages/TransactionsPage'
import WalletsPage from './pages/WalletsPage'
import GoalsPage from './pages/GoalsPage'
import BillsPage from './pages/BillsPage'
import RecurringPage from './pages/RecurringPage'
import PortfolioPage from './pages/PortfolioPage'
import HelpPage from './pages/HelpPage'
import SettingsPage from './pages/SettingsPage'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="wallets" element={<WalletsPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="bills" element={<BillsPage />} />
        <Route path="recurring" element={<RecurringPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
