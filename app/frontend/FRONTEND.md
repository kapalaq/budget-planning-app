# Frontend Architecture Guide

## Quick Start

```bash
cd app/frontend
npm install
npm run dev        # starts on http://localhost:3000
```

The dev server proxies all `/api/*` requests to `http://localhost:8000` (the FastAPI backend), so both must be running.

**Production build:**

```bash
npm run build      # outputs to dist/
```

---

## Tech Stack

| Layer       | Tool                     |
|-------------|--------------------------|
| Framework   | React 19 + Vite          |
| Routing     | react-router-dom v7      |
| Charts      | Recharts                 |
| Icons       | lucide-react             |
| Styling     | Plain CSS (no framework) |
| State       | React hooks (no Redux)   |

---

## Project Structure

```
src/
├── api/
│   └── client.js            # All HTTP calls to backend
├── context/
│   └── AuthContext.jsx       # Auth state (token in localStorage)
├── hooks/
│   └── useToast.js           # Toast notification hook
├── components/
│   ├── Layout.jsx            # Sidebar + main content shell
│   ├── Modal.jsx             # Generic modal wrapper
│   ├── ConfirmDialog.jsx     # Yes/No confirmation popup
│   ├── Toast.jsx             # Toast notification renderer
│   ├── EmptyState.jsx        # Placeholder for empty lists
│   └── TransactionForm.jsx   # Reusable add/edit transaction form
├── pages/
│   ├── LoginPage.jsx         # Login / register
│   ├── DashboardPage.jsx     # Main dashboard with stats + charts
│   ├── TransactionsPage.jsx  # Transaction list + transfers
│   ├── WalletsPage.jsx       # Wallet grid + switch/add/delete
│   ├── GoalsPage.jsx         # Savings goals with progress
│   ├── BillsPage.jsx         # Bills tracking
│   ├── RecurringPage.jsx     # Recurring transaction list
│   └── SettingsPage.jsx      # Language + timezone
├── App.jsx                   # Route definitions
├── App.css                   # All component styles
├── index.css                 # CSS variables (theme), resets
└── main.jsx                  # Entry point
```

---

## How the Pieces Connect

```
main.jsx
  └─ BrowserRouter
       └─ AuthProvider          (provides login/logout + token)
            └─ App.jsx          (route definitions)
                 ├─ /login  →  LoginPage
                 └─ /       →  Layout (sidebar + Outlet)
                      ├─ index        →  DashboardPage
                      ├─ transactions →  TransactionsPage
                      ├─ wallets      →  WalletsPage
                      ├─ goals        →  GoalsPage
                      ├─ bills        →  BillsPage
                      ├─ recurring    →  RecurringPage
                      └─ settings     →  SettingsPage
```

**Data flow in a page:**

1. Page component mounts → calls `api.someEndpoint()` from `api/client.js`
2. `client.js` adds the Bearer token from `localStorage` and makes `fetch()` call
3. Vite proxy rewrites `/api/dashboard` → `http://localhost:8000/dashboard`
4. Response arrives → page sets state → React re-renders

---

## API Client (`src/api/client.js`)

All backend communication goes through this single file. Every method returns a Promise that resolves to the JSON response.

```js
import api from '../api/client'

// Examples:
const res = await api.getDashboard()       // GET /dashboard
const res = await api.addTransaction(data) // POST /transactions
const res = await api.deleteWallet(name)   // DELETE /wallets/{name}
```

**Auth** is automatic — the client reads the token from `localStorage` and injects the `Authorization: Bearer <token>` header. If a 401 is returned, it clears the token and redirects to `/login`.

---

## Styling

There is **no CSS framework** — everything is plain CSS using CSS variables for theming.

### Theme variables (`index.css`)

```css
--bg-primary: #0d1b0e;     /* darkest background */
--bg-card: #1e3320;         /* card surfaces */
--accent: #4a9e5c;          /* primary green */
--income: #5cb870;          /* green for income */
--expense: #c75454;         /* red for expenses */
--transfer: #5a8dc7;        /* blue for transfers */
--text-primary: #d4e8d0;    /* main text */
```

To change the color scheme, edit the `:root` variables in `index.css`.

### CSS classes (`App.css`)

Reusable classes you'll use in new components:

| Class               | Purpose                                |
|---------------------|----------------------------------------|
| `.card`             | Card container with border + bg        |
| `.btn .btn-primary` | Primary green button                   |
| `.btn .btn-secondary` | Subtle bordered button               |
| `.btn .btn-danger`  | Red destructive button                 |
| `.btn-sm`           | Smaller button variant                 |
| `.btn-icon`         | Icon-only button (no text)             |
| `.form-group`       | Form field wrapper                     |
| `.form-input`       | Styled input/select                    |
| `.badge`            | Small pill label (`.income`, `.expense`, `.active`) |
| `.stats-grid`       | Auto-fit grid for stat cards           |
| `.stat-card`        | Individual stat with label + value     |
| `.transaction-row`  | Grid row for transaction list          |
| `.progress-bar`     | Progress bar container (`.fill` inside)|
| `.empty-state`      | Centered empty placeholder             |
| `.fade-in`          | Fade-in animation class                |

---

## Common Patterns

### Adding a toast notification

```jsx
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'

function MyPage() {
  const { toasts, success, error } = useToast()

  const doSomething = async () => {
    try {
      await api.someAction()
      success('It worked!')
    } catch (err) {
      error(err.message)
    }
  }

  return (
    <>
      <ToastContainer toasts={toasts} />
      {/* ... */}
    </>
  )
}
```

### Opening a modal

```jsx
import Modal from '../components/Modal'

const [showModal, setShowModal] = useState(false)

{showModal && (
  <Modal title="My Modal" onClose={() => setShowModal(false)}>
    <p>Content here</p>
    <div className="modal-actions">
      <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
      <button className="btn btn-primary" onClick={handleSave}>Save</button>
    </div>
  </Modal>
)}
```

### Confirm before destructive action

```jsx
import ConfirmDialog from '../components/ConfirmDialog'

const [deleteTarget, setDeleteTarget] = useState(null)

{deleteTarget && (
  <ConfirmDialog
    title="Delete Item"
    message={`Are you sure you want to delete "${deleteTarget}"?`}
    onConfirm={handleDelete}
    onCancel={() => setDeleteTarget(null)}
    danger
  />
)}
```

---

## How to Add a New Feature

### 1. New API endpoint

If the backend has a new endpoint, add the method to `src/api/client.js`:

```js
// In the api object:
getMyFeature: () => request('GET', '/my-feature'),
doMyAction: (data) => request('POST', '/my-feature', data),
```

### 2. New page

Create `src/pages/MyFeaturePage.jsx`:

```jsx
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import { useToast } from '../hooks/useToast'
import ToastContainer from '../components/Toast'

export default function MyFeaturePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toasts, success, error: showError } = useToast()

  const load = useCallback(async () => {
    try {
      const res = await api.getMyFeature()
      setData(res.data)
    } catch (err) { showError(err.message) }
    finally { setLoading(false) }
  }, [showError])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="loading-page"><div className="spinner" /></div>

  return (
    <>
      <ToastContainer toasts={toasts} />
      <div className="page-header"><h2>My Feature</h2></div>
      <div className="page-content fade-in">
        {/* your content */}
      </div>
    </>
  )
}
```

### 3. Register the route

In `src/App.jsx`, add:

```jsx
import MyFeaturePage from './pages/MyFeaturePage'

// Inside the Layout route:
<Route path="my-feature" element={<MyFeaturePage />} />
```

### 4. Add sidebar link

In `src/components/Layout.jsx`, add to the `navItems` array:

```jsx
import { Star } from 'lucide-react'

const navItems = [
  // ... existing items
  { to: '/my-feature', icon: Star, label: 'My Feature' },
]
```

### 5. New reusable component

Create in `src/components/MyComponent.jsx` and import where needed. Follow the pattern of existing components — they take props, return JSX, and use CSS classes from `App.css`.

---

## Key Files to Edit

| Want to...                  | Edit                          |
|-----------------------------|-------------------------------|
| Add backend API call        | `src/api/client.js`           |
| Change colors/theme         | `src/index.css` (`:root`)     |
| Change component styles     | `src/App.css`                 |
| Add a new page              | `src/pages/` + `App.jsx`      |
| Add sidebar link            | `src/components/Layout.jsx`   |
| Change auth behavior        | `src/context/AuthContext.jsx`  |
| Change proxy target         | `vite.config.js`              |
