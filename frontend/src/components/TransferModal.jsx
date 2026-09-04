import React, { useState, useEffect } from 'react';
import { X, Send, AlertCircle, CheckCircle2, UserCheck, ArrowRight, ShieldCheck } from 'lucide-react';
import { bankingApi, DEFAULT_TRANSFER_OTP } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const TransferModal = ({ isOpen, onClose, onSuccess, initialData = null }) => {
  const { account, refreshAccount } = useAuth();
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Transfer');
  const [otp, setOtp] = useState(DEFAULT_TRANSFER_OTP);
  const [recipientInfo, setRecipientInfo] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (initialData) {
      setToAccount(initialData.to_account_number || '');
      setAmount(initialData.amount_dollars ? String(initialData.amount_dollars) : '');
      setDescription(initialData.description || 'AI Initiated Transfer');
      setCategory(initialData.category || 'Transfer');
      setOtp(DEFAULT_TRANSFER_OTP);
      if (initialData.to_account_number) {
        verifyRecipient(initialData.to_account_number);
      }
    } else {
      setToAccount('');
      setAmount('');
      setDescription('');
      setCategory('Transfer');
      setOtp(DEFAULT_TRANSFER_OTP);
      setRecipientInfo(null);
      setError('');
      setSuccess(false);
    }
  }, [initialData, isOpen]);

  const verifyRecipient = async (accNum) => {
    if (!accNum || accNum.length < 5) return;
    setLookupLoading(true);
    setError('');
    try {
      const res = await bankingApi.lookupAccount(accNum.trim());
      setRecipientInfo(res);
    } catch (e) {
      setRecipientInfo(null);
      setError('Recipient account not found. Please verify the account number.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleToAccountBlur = () => {
    verifyRecipient(toAccount);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const amt = parseFloat(amount);
    if (isNaN(amt) || amt <= 0) {
      setError('Please enter a valid amount greater than $0.00');
      return;
    }

    if (account && amt * 100 > account.balance_cents) {
      setError('Insufficient funds for this transfer.');
      return;
    }

    if (!otp || otp.trim().length !== 6) {
      setError('Please enter the 6-digit confirmation OTP.');
      return;
    }

    setLoading(true);
    try {
      await bankingApi.transfer(toAccount.trim(), amt, description, category, otp.trim());
      setSuccess(true);
      await refreshAccount();
      if (onSuccess) onSuccess();
      setTimeout(() => {
        onClose();
        setSuccess(false);
      }, 1200);
    } catch (err) {
      setError(err.response?.data?.error || 'Transfer failed. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0f1117] border border-white/[0.12] rounded-2xl w-full max-w-md p-5 sm:p-6 shadow-2xl relative max-h-[92vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Send className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Send Funds</h3>
              <p className="text-[10px] text-slate-500 font-mono">Real-time domestic wire</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-white/[0.06] transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Demo Quick Shortcuts */}
        <div className="my-3 p-2.5 rounded-xl bg-black/40 border border-white/[0.06] text-xs text-slate-400">
          <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500 block mb-1.5">Quick Demo Beneficiaries</span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => { setToAccount('ACC-83920194'); verifyRecipient('ACC-83920194'); }}
              className="px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 font-mono text-[11px] border border-white/[0.06] cursor-pointer"
            >
              Sarah Smith (ACC-83920194)
            </button>
            <button
              type="button"
              onClick={() => { setToAccount('ACC-54910283'); verifyRecipient('ACC-54910283'); }}
              className="px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 font-mono text-[11px] border border-white/[0.06] cursor-pointer"
            >
              Alice Johnson (ACC-54910283)
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0" />
            <span>Transfer authorized! Funds debited and dispatched.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          {/* Recipient Account */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Recipient Account Number</label>
            <div className="relative">
              <input
                type="text"
                required
                value={toAccount}
                onChange={(e) => setToAccount(e.target.value)}
                onBlur={handleToAccountBlur}
                placeholder="e.g. ACC-83920194"
                className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs font-mono"
              />
              <button
                type="button"
                onClick={() => verifyRecipient(toAccount)}
                disabled={lookupLoading}
                className="absolute right-2.5 top-2 text-[11px] text-emerald-400 hover:text-emerald-300 font-medium cursor-pointer"
              >
                {lookupLoading ? 'Verifying...' : 'Verify'}
              </button>
            </div>

            {recipientInfo && (
              <div className="mt-1.5 p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center space-x-1.5">
                <UserCheck className="h-3.5 w-3.5" />
                <span>Verified: <strong>{recipientInfo.owner_name}</strong> ({recipientInfo.status})</span>
              </div>
            )}
          </div>

          {/* Amount */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Transfer Amount ($ USD)</label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-slate-500 font-mono text-xs">$</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full pl-7 pr-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs font-mono"
              />
            </div>
            {account && (
              <span className="text-[10px] text-slate-500 mt-1 block font-mono">
                Available Liquidity: ${(account.balance_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Expense Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 focus:outline-none focus:border-emerald-500/60 text-xs"
            >
              <option value="Transfer">Transfer</option>
              <option value="Dining">Dining</option>
              <option value="Housing">Housing</option>
              <option value="Groceries">Groceries</option>
              <option value="Utilities">Utilities</option>
              <option value="Shopping">Shopping</option>
              <option value="Transportation">Transportation</option>
              <option value="Gift">Gift</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Transfer Memo</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Wire, Invoice split"
              className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs"
            />
          </div>

          {/* Confirmation OTP Gate Card */}
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-amber-400">
                <ShieldCheck className="h-3.5 w-3.5" />
                <label className="text-[11px] font-semibold">Confirmation OTP Gate</label>
              </div>
              <button
                type="button"
                onClick={() => setOtp(DEFAULT_TRANSFER_OTP)}
                className="text-[10px] text-amber-300 hover:text-amber-200 underline font-mono cursor-pointer"
              >
                Autofill Demo OTP ({DEFAULT_TRANSFER_OTP})
              </button>
            </div>
            <input
              type="text"
              required
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="Enter 6-digit confirmation OTP"
              className="w-full px-3 py-2 bg-black/50 border border-amber-500/30 rounded-lg text-amber-200 placeholder-amber-500/40 focus:outline-none focus:border-amber-400 text-xs font-mono tracking-widest text-center"
            />
            <span className="text-[10px] text-slate-500 block text-center font-mono">
              2FA protection active • Configured in .env
            </span>
          </div>

          {/* Actions */}
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
              <span>{loading ? 'Dispatched...' : 'Confirm Transfer'}</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
