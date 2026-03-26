import { useState } from 'react'
import {
  HelpCircle, LayoutDashboard, ArrowLeftRight, Wallet, Target, Receipt,
  Repeat, PieChart, Settings, LogIn, ChevronDown, ChevronRight,
  Plus, Edit3, Trash2, Send, Filter, DollarSign, CheckCircle, EyeOff,
  RotateCcw, Globe, Clock,
} from 'lucide-react'

function Section({ icon: Icon, title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        {open ? <ChevronDown size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} /> : <ChevronRight size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />}
        <Icon size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
        <div className="card-title" style={{ margin: 0 }}>{title}</div>
      </div>
      {open && <div style={{ marginTop: 16, paddingLeft: 4 }}>{children}</div>}
    </div>
  )
}

function Tip({ children }) {
  return (
    <div style={{
      padding: '10px 14px', background: 'var(--bg-tertiary)', borderLeft: '3px solid var(--accent)',
      borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--text-secondary)',
      marginTop: 12, marginBottom: 12,
    }}>
      {children}
    </div>
  )
}

function IconLabel({ icon: Icon, children }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600, color: 'var(--text-primary)' }}>
      <Icon size={14} /> {children}
    </span>
  )
}

function SubHeading({ children }) {
  return <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-bright)', marginTop: 16, marginBottom: 8 }}>{children}</div>
}

function Paragraph({ children }) {
  return <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: '6px 0' }}>{children}</p>
}

function BulletList({ items }) {
  return (
    <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
      {items.map((item, i) => (
        <li key={i} style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{item}</li>
      ))}
    </ul>
  )
}

export default function HelpPage() {
  return (
    <>
      <div className="page-header">
        <h2><HelpCircle size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 8 }} />Help & Guide</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 4 }}>
          Everything you need to know about using Budget Planner
        </p>
      </div>

      <div className="page-content fade-in" style={{ maxWidth: 800, width: '100%' }}>

        {/* Getting Started */}
        <Section icon={LogIn} title="Getting Started" defaultOpen={true}>
          <SubHeading>Creating an Account</SubHeading>
          <Paragraph>
            On the login screen, click "Don't have an account? Register" to switch to registration mode.
            Enter a username and password, then click "Create Account". You'll be logged in automatically.
          </Paragraph>
          <SubHeading>Signing In</SubHeading>
          <Paragraph>
            Enter your username and password on the login page and click "Sign In".
            Your session is saved in the browser — you'll stay logged in until you sign out.
          </Paragraph>
          <SubHeading>Signing Out</SubHeading>
          <Paragraph>
            Click the "Sign Out" button at the bottom of the sidebar to log out and return to the login screen.
          </Paragraph>
          <Tip>Your data is stored per-account on the server. You can log in from any device and see the same wallets, transactions, and goals.</Tip>
        </Section>

        {/* Dashboard */}
        <Section icon={LayoutDashboard} title="Dashboard">
          <Paragraph>
            The Dashboard is your home screen. It shows an overview of your currently active wallet including balance, total income, total expenses, spending breakdowns, active goals, and recent transactions.
          </Paragraph>
          <SubHeading>Stats Cards</SubHeading>
          <Paragraph>
            At the top you'll see three summary cards: your current <strong>Balance</strong>, total <strong>Income</strong>, and total <strong>Expenses</strong> for the active wallet.
          </Paragraph>
          <SubHeading>Category Charts</SubHeading>
          <Paragraph>
            Pie charts show how your expenses and income break down by category. Hover over a slice to see the exact amount. The legend below each chart maps colors to category names.
          </Paragraph>
          <SubHeading>Active Goals</SubHeading>
          <Paragraph>
            If you have active savings goals, they appear as progress cards showing how much you've saved toward each target.
          </Paragraph>
          <SubHeading>Quick Actions</SubHeading>
          <BulletList items={[
            <><IconLabel icon={Plus}>Add Transaction</IconLabel> — click the button in the top-right to quickly add a new transaction to the active wallet.</>,
            <><IconLabel icon={Edit3}>Edit</IconLabel> / <IconLabel icon={Trash2}>Delete</IconLabel> — use the icons on each transaction row to modify or remove it. Transfer transactions cannot be edited or deleted individually.</>,
          ]} />
          <Tip>The dashboard automatically processes any pending recurring transactions each time you visit it, so your data is always up to date.</Tip>
        </Section>

        {/* Transactions */}
        <Section icon={ArrowLeftRight} title="Transactions">
          <Paragraph>
            The Transactions page shows all transactions in your active wallet. From here you can add, edit, delete transactions and make transfers between wallets.
          </Paragraph>
          <SubHeading>Adding a Transaction</SubHeading>
          <BulletList items={[
            'Click the "Add" button in the top-right corner.',
            'Choose the type: Expense or Income.',
            'Select a category from the list (categories are predefined based on the type).',
            'Enter the amount and an optional description.',
            'Optionally change the date (defaults to today).',
            'Click "Add" to save.',
          ]} />
          <SubHeading>Editing & Deleting</SubHeading>
          <Paragraph>
            Each transaction row has edit and delete buttons on the right side. Click <IconLabel icon={Edit3}>Edit</IconLabel> to open the transaction in a form where you can modify any field. Click <IconLabel icon={Trash2}>Delete</IconLabel> to remove it (you'll be asked to confirm).
          </Paragraph>
          <Tip>Transfer transactions (marked with a double-arrow icon) cannot be edited or deleted from the transaction list. Delete the transfer from the wallet that initiated it.</Tip>
          <SubHeading>Transfers</SubHeading>
          <Paragraph>
            Click <IconLabel icon={Send}>Transfer</IconLabel> to move money between wallets. Select the destination wallet and enter the amount. If the wallets use different currencies, you can specify the received amount in the target currency.
          </Paragraph>
          <SubHeading>Filters</SubHeading>
          <Paragraph>
            When filters are active, a yellow banner shows how many transactions match out of the total. Click "Clear Filters" to remove all active filters and see every transaction again.
          </Paragraph>
        </Section>

        {/* Wallets */}
        <Section icon={Wallet} title="Wallets">
          <Paragraph>
            Wallets let you organize your money by account, purpose, or currency. Each wallet has its own balance, transactions, and currency.
          </Paragraph>
          <SubHeading>Your Wallets</SubHeading>
          <Paragraph>
            All your wallets appear as cards showing the wallet name, balance, transaction count, and currency. The currently active wallet is highlighted with a green "Active" badge.
          </Paragraph>
          <SubHeading>Switching Wallets</SubHeading>
          <Paragraph>
            Click on any wallet card to switch to it. The Dashboard and Transactions pages will then show data for that wallet.
          </Paragraph>
          <SubHeading>Creating a Wallet</SubHeading>
          <BulletList items={[
            'Click "Add Wallet" in the top-right corner.',
            'Enter a name for the wallet.',
            'Choose a currency (USD, EUR, GBP, KZT, RUB, JPY, CNY, TRY, BRL, INR).',
            'Optionally add a description.',
            'Click "Create".',
          ]} />
          <SubHeading>Deleting a Wallet</SubHeading>
          <Paragraph>
            Click the trash icon on a wallet card to delete it. You cannot delete the currently active wallet — switch to a different wallet first.
          </Paragraph>
          <Tip>Deleting a wallet permanently removes all its transactions. This cannot be undone.</Tip>
        </Section>

        {/* Goals */}
        <Section icon={Target} title="Savings Goals">
          <Paragraph>
            Goals help you track progress toward a savings target. Each goal has a name, target amount, currency, and progress bar showing how close you are.
          </Paragraph>
          <SubHeading>Creating a Goal</SubHeading>
          <BulletList items={[
            'Click "Add Goal" and fill in the name, target amount, currency, and optional description.',
            'The goal starts in "active" status with 0 saved.',
          ]} />
          <SubHeading>Saving Toward a Goal</SubHeading>
          <Paragraph>
            Click <IconLabel icon={DollarSign}>Save</IconLabel> on an active goal card to add money toward it. Enter the amount and click "Save". The progress bar updates automatically.
          </Paragraph>
          <SubHeading>Goal Lifecycle</SubHeading>
          <BulletList items={[
            <><IconLabel icon={CheckCircle}>Complete</IconLabel> — marks the goal as completed regardless of progress. Completed goals can be deleted.</>,
            <><IconLabel icon={EyeOff}>Hide</IconLabel> — hides the goal from the active list. Hidden goals can be deleted or reactivated.</>,
            <><IconLabel icon={RotateCcw}>Reactivate</IconLabel> — brings a hidden goal back to active status.</>,
            <><IconLabel icon={Trash2}>Delete</IconLabel> — permanently deletes a completed or hidden goal and all saved progress.</>,
          ]} />
          <SubHeading>Filtering</SubHeading>
          <Paragraph>
            Use the "Active" / "All" tabs at the top to toggle between showing only active goals or all goals including completed and hidden ones.
          </Paragraph>
          <Tip>You can only delete goals that are completed or hidden — not active ones. Hide or complete a goal first if you want to remove it.</Tip>
        </Section>

        {/* Bills */}
        <Section icon={Receipt} title="Bills">
          <Paragraph>
            Bills work like goals but for upcoming payments. Track how much you've set aside toward a bill and mark it paid when done.
          </Paragraph>
          <SubHeading>Creating a Bill</SubHeading>
          <BulletList items={[
            'Click "Add Bill" and enter the bill name, amount due, currency, and optional description.',
            'The bill starts in "active" status.',
          ]} />
          <SubHeading>Paying a Bill</SubHeading>
          <Paragraph>
            Click <IconLabel icon={DollarSign}>Pay</IconLabel> on an active bill to record a payment toward it. The progress bar shows how much of the total amount has been paid.
          </Paragraph>
          <SubHeading>Bill Lifecycle</SubHeading>
          <Paragraph>
            Bills follow the same lifecycle as goals: Active → Completed/Hidden → Deletable. Use <IconLabel icon={CheckCircle}>Complete</IconLabel> to mark a bill as fully paid, <IconLabel icon={EyeOff}>Hide</IconLabel> to archive it, and <IconLabel icon={RotateCcw}>Reactivate</IconLabel> to bring it back.
          </Paragraph>
          <Tip>Use the "Active" / "All" tabs to switch between viewing only active bills or all bills.</Tip>
        </Section>

        {/* Recurring */}
        <Section icon={Repeat} title="Recurring Transactions">
          <Paragraph>
            Recurring transactions are automatically created on a schedule. Use them for regular income (salary), subscriptions, rent, or any other repeating payment.
          </Paragraph>
          <SubHeading>Adding a Recurring Transaction</SubHeading>
          <BulletList items={[
            'Click "Add Recurring" and choose expense or income.',
            'Select a category and enter the amount.',
            'Set the recurrence schedule: frequency (daily, weekly, monthly, yearly) and interval (e.g., every 2 weeks).',
            'For weekly frequency, you can select specific days of the week.',
            'Add an optional description, then click "Create".',
          ]} />
          <SubHeading>Recurring Transfers</SubHeading>
          <Paragraph>
            Click <IconLabel icon={Send}>Recurring Transfer</IconLabel> to set up an automatic transfer between wallets on a schedule. Choose the destination wallet, amount, and recurrence rule.
          </Paragraph>
          <SubHeading>How Processing Works</SubHeading>
          <Paragraph>
            Recurring transactions are processed automatically each time you visit the Dashboard. Any transactions that are overdue based on their schedule will be created as real transactions in your wallet.
          </Paragraph>
          <SubHeading>Managing</SubHeading>
          <Paragraph>
            Each recurring transaction shows its category, description, amount, schedule pattern, and whether it's active or paused. Click the trash icon to delete a recurring rule.
          </Paragraph>
        </Section>

        {/* Portfolio */}
        <Section icon={PieChart} title="Portfolio">
          <Paragraph>
            The Portfolio page gives you a birds-eye view of your total wealth across all wallets, converted to a single base currency.
          </Paragraph>
          <SubHeading>What You'll See</SubHeading>
          <BulletList items={[
            'Total Balance — the sum of all wallet balances converted to your base currency.',
            'Wallet Count — how many wallets you have.',
            'Base Currency — the currency used for conversion.',
            'Balance Distribution Chart — a pie chart showing the proportion of each wallet.',
            'Wallet Breakdown — a detailed list showing each wallet\'s native balance and its converted equivalent.',
          ]} />
          <Tip>If some exchange rates are unavailable, a warning banner will appear. Amounts may be approximate in that case.</Tip>
        </Section>

        {/* Settings */}
        <Section icon={Settings} title="Settings">
          <Paragraph>
            The Settings page lets you configure your account preferences.
          </Paragraph>
          <SubHeading><IconLabel icon={Globe}>Language</IconLabel></SubHeading>
          <Paragraph>
            Choose between English, Russian, and Kazakh. This changes the language used for categories and system messages.
          </Paragraph>
          <SubHeading><IconLabel icon={Clock}>Timezone</IconLabel></SubHeading>
          <Paragraph>
            Set your timezone as a GMT offset (from GMT-12 to GMT+14). This affects how dates and recurring transaction schedules are calculated.
          </Paragraph>
        </Section>

        {/* Tips & Tricks */}
        <Section icon={HelpCircle} title="Tips & Tricks">
          <SubHeading>Multi-Currency Workflow</SubHeading>
          <Paragraph>
            Create separate wallets for each currency you use. When transferring between wallets with different currencies, you can specify both the sent amount and received amount to account for exchange rates.
          </Paragraph>
          <SubHeading>Organize with Categories</SubHeading>
          <Paragraph>
            Categories are predefined and differ between income and expense types. Consistently using categories helps the Dashboard pie charts give you meaningful spending insights.
          </Paragraph>
          <SubHeading>Use Recurring for Automation</SubHeading>
          <Paragraph>
            Set up recurring transactions for predictable income and expenses like salary, rent, or subscriptions. They're processed automatically when you open the app.
          </Paragraph>
          <SubHeading>Goal vs Bill</SubHeading>
          <Paragraph>
            Use <strong>Goals</strong> for things you're saving up for (vacation, emergency fund).
            Use <strong>Bills</strong> for obligations you need to pay (rent, utilities, invoices).
          </Paragraph>
          <SubHeading>Mobile Access</SubHeading>
          <Paragraph>
            The interface is fully responsive. On smaller screens, the sidebar collapses into a menu button in the top-left corner.
          </Paragraph>
        </Section>

      </div>
    </>
  )
}
