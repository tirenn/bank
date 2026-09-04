import React, { useState } from 'react';
import { X, Plus, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { bankingApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { formatHumanReadableError } from '../utils/formatError';

export const DepositModal = ({ isOpen, onClose, onSuccess }) => {
  const { refreshAccount } = useAuth();
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('Checking Account Deposit');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const amt = parseFloat(amount);
    if (isNaN(amt) || amt <= 0) {
      setError('Please enter a valid amount greater than $0.00');
      return;
    }

    setLoading(true);
    try {
      await bankingApi.deposit(amt, description, 'Deposit');
      setSuccess(true);
      await refreshAccount();
      if (onSuccess) onSuccess();
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setAmount('');
      }, 1200);
    } catch (err) {
      setError(formatHumanReadableError(err, 'Deposit failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0f1117] border border-white/[0.12] rounded-2xl w-full max-w-md p-5 sm:p-6 shadow-2xl relative max-h-[92vh] overflow-y-auto">
        
        <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-white/[0.06] border border-white/[0.08] text-slate-200">
              <Plus className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Add Account Balance</h3>
              <p className="text-[10px] text-slate-500 font-mono">Instant liquidity credit</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-white/[0.06] transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="my-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="my-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0" />
            <span>Deposit completed successfully. Funds available.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-3.5 space-y-3.5">
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Deposit Amount ($ USD)</label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-slate-500 font-mono text-xs">$</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="100.00"
                className="w-full pl-7 pr-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Deposit Memo</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs"
            />
          </div>

          <div className="pt-2 flex items-center justify-end space-x-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || success}
              className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-all shadow-sm disabled:opacity-50 cursor-pointer flex items-center space-x-1"
            >
              <span>{loading ? 'Processing...' : 'Deposit Funds'}</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
