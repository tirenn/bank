import React, { useState } from 'react';
import { Eye, EyeOff, Copy, Check, ArrowUpRight, Plus, CreditCard, ShieldCheck, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { copyToClipboard } from '../utils/clipboard';
import { DEFAULT_TRANSFER_OTP } from '../services/api';

export const AccountCard = ({ onTransferClick, onDepositClick }) => {
  const { user, account, accounts, selectAccount } = useAuth();
  const [showBalance, setShowBalance] = useState(true);
  const [showCardDetails, setShowCardDetails] = useState(false);
  const [copiedAcc, setCopiedAcc] = useState(false);
  const [copiedCard, setCopiedCard] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const balance = account
    ? (account.balance_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '0.00';
  const accNumber = account?.account_number || 'ACC-00000000';
  const accName = account?.account_name || 'Primary Account';
  const accType = account?.account_type || 'CHECKING';
  const rawCardNumber = account?.card_number || '4532 8920 1823 9042';
  const cardBrand = (account?.card_brand || 'VISA').toUpperCase();
  const cardExpiry = account?.card_expiry || '08/29';
  const cardCVV = account?.card_cvv || '832';

  const maskedCardNumber = rawCardNumber.length >= 19
    ? `${rawCardNumber.slice(0, 4)} •••• •••• ${rawCardNumber.slice(-4)}`
    : rawCardNumber;

  const copyAccToClipboard = async () => {
    const success = await copyToClipboard(accNumber);
    if (success) {
      setCopiedAcc(true);
      setTimeout(() => setCopiedAcc(false), 2000);
    }
  };

  const copyCardToClipboard = async () => {
    const success = await copyToClipboard(rawCardNumber.replace(/\s+/g, ''));
    if (success) {
      setCopiedCard(true);
      setTimeout(() => setCopiedCard(false), 2000);
    }
  };


  return (
    <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 sm:p-7 shadow-lg flex flex-col justify-between h-full space-y-5">
      
      {/* Top bar: Multi-Account Selector & Status */}
      <div className="flex items-center justify-between relative">
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center space-x-2 text-left p-1.5 -m-1.5 rounded-xl hover:bg-white/[0.05] transition-colors cursor-pointer"
          >
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CreditCard className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-semibold text-slate-100">{accName}</span>
                {accounts && accounts.length > 1 && (
                  <ChevronDown className="h-3 w-3 text-slate-400" />
                )}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {account?.currency || 'USD'} • {accType} ({accounts?.length || 1} Accounts)
              </div>
            </div>
          </button>

          {/* Accounts Dropdown */}
          {showDropdown && accounts && accounts.length > 1 && (
            <div className="absolute top-full left-0 mt-2 w-72 bg-[#161922] border border-white/[0.12] rounded-xl shadow-2xl p-2 z-50 backdrop-blur-md">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 px-3 py-1 font-semibold">
                Switch Bank Account
              </div>
              <div className="space-y-1 mt-1">
                {accounts.map((acc) => (
                  <button
                    key={acc.id}
                    onClick={() => {
                      selectAccount(acc);
                      setShowDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-center justify-between cursor-pointer ${
                      acc.id === account?.id
                        ? 'bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/30'
                        : 'text-slate-300 hover:bg-white/[0.05]'
                    }`}
                  >
                    <div>
                      <div>{acc.account_name || 'Account'}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{acc.account_number} • {acc.card_brand || 'VISA'}</div>
                    </div>
                    <div className="font-mono text-xs">
                      ${(acc.balance_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5" />
            {account?.status || 'ACTIVE'}
          </span>
        </div>
      </div>

      {/* Modern Visual Credit / Debit Card Mockup */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-tr from-[#131620] via-[#1a2030] to-[#252b42] p-5 border border-white/[0.12] shadow-inner text-white space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* EMV Chip SVG */}
            <div className="w-9 h-7 rounded bg-gradient-to-br from-amber-200 via-amber-400 to-amber-600 border border-amber-300/40 flex items-center justify-center shadow-sm">
              <div className="w-5 h-4 border border-amber-800/40 rounded-sm grid grid-cols-2 grid-rows-2 opacity-60"></div>
            </div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-300 font-bold">
              {accType} DEBIT
            </span>
          </div>
          <div className="text-right">
            <span className="text-sm font-black italic tracking-wider font-mono text-emerald-400">
              {cardBrand}
            </span>
          </div>
        </div>

        {/* 16-Digit Card Number with Copy & Mask Toggle */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[9px] uppercase font-mono tracking-widest text-slate-400">Card Number</span>
            <button
              onClick={() => setShowCardDetails(!showCardDetails)}
              className="text-[10px] text-slate-400 hover:text-white flex items-center space-x-1 cursor-pointer"
            >
              {showCardDetails ? <EyeOff className="h-3 w-3 mr-1" /> : <Eye className="h-3 w-3 mr-1" />}
              <span>{showCardDetails ? 'Hide' : 'Show'}</span>
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-mono text-sm sm:text-base tracking-[0.18em] text-slate-100 font-semibold">
              {showCardDetails ? rawCardNumber : maskedCardNumber}
            </span>
            <button
              onClick={copyCardToClipboard}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/[0.1] transition-colors cursor-pointer"
              title="Copy card number"
            >
              {copiedCard ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        {/* Cardholder, Expiry & CVV */}
        <div className="flex items-end justify-between pt-1 border-t border-white/[0.08] text-[10px] font-mono">
          <div>
            <div className="text-[9px] text-slate-400 uppercase">Cardholder</div>
            <div className="font-semibold text-slate-200 tracking-wide uppercase">{user?.full_name || 'JOHN DOE'}</div>
          </div>
          <div className="text-center">
            <div className="text-[9px] text-slate-400 uppercase">Expires</div>
            <div className="font-semibold text-slate-200">{cardExpiry}</div>
          </div>
          <div className="text-right">
            <div className="text-[9px] text-slate-400 uppercase">CVV</div>
            <div className="font-semibold text-slate-200">{showCardDetails ? cardCVV : '•••'}</div>
          </div>
        </div>
      </div>

      {/* Available Balance Hero */}
      <div className="space-y-1">
        <div className="flex items-center space-x-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
          <span>Available Account Balance</span>
          <button
            onClick={() => setShowBalance(!showBalance)}
            className="text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
            title={showBalance ? "Hide balance" : "Show balance"}
          >
            {showBalance ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
          </button>
        </div>

        <div className="text-3xl sm:text-4xl font-semibold text-white tracking-tight flex items-baseline space-x-1.5 font-mono">
          <span className="text-slate-400 text-2xl font-light">$</span>
          <span>{showBalance ? balance : '••••••••'}</span>
          <span className="text-xs font-normal text-slate-500 font-sans">{account?.currency || 'USD'}</span>
        </div>
      </div>

      {/* Transfer OTP Gate Security Banner */}
      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-4 w-4 text-amber-400 flex-shrink-0" />
          <div>
            <div className="text-[11px] font-semibold text-amber-300">Transfer Confirmation Gate Active</div>
            <div className="text-[10px] text-amber-400/80 font-mono">2FA Protection required for all outgoing wires</div>
          </div>
        </div>
        <div className="flex items-center space-x-1.5 bg-black/40 px-2.5 py-1 rounded-lg border border-amber-500/30">
          <span className="text-[9px] uppercase tracking-wider text-amber-500 font-mono">Demo OTP:</span>
          <span className="font-mono text-xs font-bold text-amber-300 tracking-widest">{DEFAULT_TRANSFER_OTP}</span>
        </div>
      </div>

      {/* Bottom Bar: Account Number & Action Triggers */}
      <div className="pt-3 border-t border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">Account Number</span>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-slate-200 font-medium text-xs tracking-wider">{accNumber}</span>
            <button
              onClick={copyAccToClipboard}
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition-colors cursor-pointer"
              title="Copy account number"
            >
              {copiedAcc ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <button
            onClick={onDepositClick}
            className="flex-1 sm:flex-initial justify-center px-3.5 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.08] text-slate-200 font-medium text-xs transition-colors border border-white/[0.08] flex items-center space-x-1.5 cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Deposit</span>
          </button>
          <button
            onClick={onTransferClick}
            className="flex-1 sm:flex-initial justify-center px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-all flex items-center space-x-1.5 cursor-pointer shadow-sm"
          >
            <span>Transfer</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

    </div>
  );
};

