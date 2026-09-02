import React, { useState, useEffect } from 'react';
import { ArrowDownLeft, ArrowUpRight, Search, RefreshCw, Layers } from 'lucide-react';
import { bankingApi } from '../services/api';

export const TransactionList = ({ refreshTrigger }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  const fetchTxs = async () => {
    setLoading(true);
    try {
      const data = await bankingApi.getTransactions(50, 0, selectedCategory);
      setTransactions(data.transactions || []);
    } catch (e) {
      console.error('Error fetching transactions:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTxs();
  }, [refreshTrigger, selectedCategory]);

  const filtered = transactions.filter((tx) => {
    if (!search) return true;
    const query = search.toLowerCase();
    return (
      tx.description?.toLowerCase().includes(query) ||
      tx.category?.toLowerCase().includes(query) ||
      tx.counterparty_name?.toLowerCase().includes(query) ||
      tx.reference_number?.toLowerCase().includes(query)
    );
  });

  const categories = ['All', 'Salary', 'Income', 'Housing', 'Dining', 'Groceries', 'Utilities', 'Subscriptions', 'Shopping', 'Transfer', 'Deposit'];

  return (
    <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-4">
      {/* Header with Search and Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Transaction Ledger</h3>
          <p className="text-[11px] text-slate-500 font-mono">Immutable audit history</p>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Search Input */}
          <div className="relative flex-1 sm:flex-initial">
            <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by note, counterparty..."
              className="pl-8 pr-3 py-1.5 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 w-full sm:w-60 transition-colors"
            />
          </div>

          <button
            onClick={fetchTxs}
            className="p-2 sm:p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.08] text-slate-400 hover:text-slate-200 border border-white/[0.08] transition-colors cursor-pointer flex-shrink-0"
            title="Refresh transactions"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-[11px]">
        {categories.map((cat) => {
          const isSelected = (cat === 'All' && !selectedCategory) || selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat === 'All' ? '' : cat)}
              className={`px-2.5 py-1 rounded-md whitespace-nowrap transition-colors cursor-pointer font-medium ${
                isSelected
                  ? 'bg-white text-slate-950 font-semibold'
                  : 'bg-white/[0.04] text-slate-400 hover:text-slate-200 border border-white/[0.06]'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Transaction Records */}
      <div className="divide-y divide-white/[0.04]">
        {loading ? (
          <div className="py-12 text-center text-slate-500 text-xs font-mono">Querying ledger records...</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">No ledger entries match your filter.</div>
        ) : (
          filtered.map((tx) => {
            const isCredit = tx.type === 'DEPOSIT' || tx.type === 'TRANSFER_IN';
            const amount = (tx.amount_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const dateStr = new Date(tx.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            return (
              <div key={tx.id} className="py-3 flex items-center justify-between hover:bg-white/[0.02] px-2 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <div
                    className={`p-2 rounded-lg border flex items-center justify-center ${
                      isCredit
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        : 'bg-white/[0.04] border-white/[0.08] text-slate-400'
                    }`}
                  >
                    {isCredit ? <ArrowDownLeft className="h-3.5 w-3.5" /> : <ArrowUpRight className="h-3.5 w-3.5" />}
                  </div>

                  <div>
                    <div className="text-xs font-medium text-slate-200 flex items-center space-x-1.5">
                      <span>{tx.description || tx.type}</span>
                      {tx.counterparty_name && (
                        <span className="text-[11px] text-slate-400 font-normal">
                          • {tx.counterparty_name}
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-500 flex items-center space-x-2 mt-0.5 font-mono">
                      <span>{dateStr}</span>
                      <span>•</span>
                      <span className="text-slate-400 font-sans">{tx.category || 'General'}</span>
                      <span>•</span>
                      <span className="text-slate-600">{tx.reference_number}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right font-mono text-xs">
                  <div className={`font-semibold ${isCredit ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {isCredit ? '+' : '-'}${amount}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase font-sans tracking-wider">{tx.type}</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
