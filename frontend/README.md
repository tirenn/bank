# Tirenn Frontend Client (`bank-frontend`)

Modern, responsive Banking UI and AI Copilot client built with **React 19**, **Vite**, and **Tailwind CSS**.

---

## 🌟 Key Features

* **Customer Financial Dashboard**: Multi-account balances, categorized spending summaries, and real-time transaction ledger.
* **Autonomous AI Banking Copilot**: Embedded conversational assistant capable of executing chained workflows, RAG FAQ queries, and multi-turn application forms.
* **Interactive AI Action Cards**: Human-in-the-loop confirmation widgets for transfers (`TRANSFER_DRAFT`) and debit card locks (`CARD_FROZEN`).
* **Security & Card Hub**: Instant debit card freeze/unfreeze controls and daily transfer limit adjustment sliders.
* **Wealth & Calculators**: Live Forex converter with bank spread display and compound loan amortization simulator.
* **Admin AI Telemetry & Cost Dashboard**: Real-time token usage KPIs, estimated USD spend breakdown by sub-agent domain, and live audit stream table.
* **Admin Vector RAG Manager**: Ingest PDF/TXT files or raw text into ChromaDB with visual chunk inspection.

---

## 🛠️ Local Development Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server (Port 5173)
npm run dev

# Build for production
npm run build
```

---

## 🌐 Production Docker Deployment

The frontend is packaged using a multi-stage Alpine Nginx container:

```bash
docker compose up -d --build bank-frontend
```

Access the application in your browser at:
👉 **`http://localhost:5173`**
