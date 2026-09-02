import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Layers } from 'lucide-react';
import { bankingApi } from '../services/api';

export const SpendingAnalytics = ({ refreshTrigger }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSummary = async () => {
    try {
      const data = await bankingApi.getSpendingSummary();
      setSummary(data);
    } catch (e) {
      console.error('Failed to fetch summary:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [refreshTrigger]);

  if (loading || !summary) {
    return (
      <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 text-center text-slate-500 text-xs font-mono">
        Aggregating cash flow analytics...
      </div>
    );
  }

  const income = summary.total_income_cents / 100;
  const spending = summary.total_spending_cents / 100;
  const net = income - spending;
  const breakdown = summary.category_breakdown || {};

  const breakdownEntries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);

  return (
    <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Monthly Cash Flow</h3>
          <p className="text-[11px] text-slate-500 font-mono">Inflow & Category Outflows</p>
        </div>
      </div>

      {/* Income & Expense Highlights */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06]">
          <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider flex items-center space-x-1 mb-1">
            <TrendingUp className="h-3 w-3 text-emerald-400" />
            <span>Total Inflow</span>
          </span>
          <span className="text-sm font-semibold text-emerald-400 font-mono">
            +${income.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06]">
          <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider flex items-center space-x-1 mb-1">
            <TrendingDown className="h-3 w-3 text-slate-400" />
            <span>Total Outflow</span>
          </span>
          <span className="text-sm font-semibold text-slate-200 font-mono">
            -${spending.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Category Breakdown */}
      <div>
        <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Category Distribution
        </h4>

        {breakdownEntries.length === 0 ? (
          <p className="text-xs text-slate-500 py-2">No categorized outflows yet.</p>
        ) : (
          <div className="space-y-3">
            {breakdownEntries.slice(0, 5).map(([cat, cents], idx) => {
              const catAmount = cents / 100;
              const percent = spending > 0 ? Math.round((catAmount / spending) * 100) : 0;

              return (
                <div key={cat} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">{cat}</span>
                    <span className="text-slate-400 font-mono text-[11px]">${catAmount.toFixed(2)} ({percent}%)</span>
                  </div>
                  <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-300 rounded-full transition-all duration-500"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Net savings indicator */}
      <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
        <span className="text-slate-400 text-[11px]">Net Periodic Delta:</span>
        <span className={`font-mono font-semibold text-xs ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
          {net >= 0 ? '+' : '-'}${Math.abs(net).toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </div>
    </div>
  );
};
