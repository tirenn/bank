import React from 'react';
import { Send, PlusCircle, Sparkles, HelpCircle } from 'lucide-react';

export const QuickActions = ({ onTransfer, onDeposit, onAiPrompt }) => {
  const actions = [
    {
      label: 'Send Funds',
      sub: 'Domestic & wire transfer',
      icon: Send,
      onClick: onTransfer,
    },
    {
      label: 'Add Deposit',
      sub: 'Instant checking credit',
      icon: PlusCircle,
      onClick: onDeposit,
    },
    {
      label: 'Spending Audit',
      sub: 'AI financial breakdown',
      icon: Sparkles,
      onClick: () => onAiPrompt('Show my spending breakdown and monthly summary'),
    },
    {
      label: 'Banking Limits',
      sub: 'Policy & transfer terms',
      icon: HelpCircle,
      onClick: () => onAiPrompt('What are the bank transfer limits and terms?'),
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {actions.map((act, idx) => {
        const Icon = act.icon;
        return (
          <button
            key={idx}
            onClick={act.onClick}
            className="p-4 rounded-2xl bg-[#0f1117] border border-white/[0.08] hover:border-white/[0.16] hover:bg-white/[0.02] text-left transition-all flex flex-col justify-between space-y-3 cursor-pointer group"
          >
            <div className="p-2 rounded-lg w-fit bg-white/[0.05] border border-white/[0.08] text-slate-300 group-hover:text-emerald-400 transition-colors">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <div className="font-medium text-xs text-slate-200">{act.label}</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{act.sub}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
};
