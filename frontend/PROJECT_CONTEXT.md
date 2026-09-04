# Project Context: Tirenn Banking React Frontend

## Architecture & Technology Stack
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS v4 + Custom Dark Theme
- **Icons**: Lucide React
- **Design Philosophy**: Non-AI Slop, High-Craftsmanship Ergonomics (instant feedback, accessible contrast, balance privacy toggle, smooth micro-interactions)
- **State & Context**: `AuthContext.jsx` managing JWT sessions and account synchronization
- **API Clients**: Axios client with JWT auto-injection for Go Core (`http://localhost:8082`) and Python AI (`http://localhost:8083`)

## Components
- `Navbar.jsx`: Brand banner, verified status, Nova AI assistant launcher, user profile
- `AccountCard.jsx`: Balance card, show/hide toggle, account copy button, deposit/transfer CTAs
- `QuickActions.jsx`: Send money, deposit, and quick AI prompts
- `TransactionList.jsx`: Ledger table with real-time text search and category filter pills
- `SpendingAnalytics.jsx`: Inflow vs outflow visual meters and category breakdown
- `TransferModal.jsx`: Funds transfer modal with recipient auto-validation
- `DepositModal.jsx`: Cash balance deposit modal
- `AiAssistant.jsx`: Interactive AI Financial Assistant with live transfer confirmation action cards
