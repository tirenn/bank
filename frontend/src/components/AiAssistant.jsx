import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, Send, Bot, User, Settings, ArrowRight, CheckCircle2, RefreshCw, Key, ShieldCheck, RotateCcw, Copy, Check } from 'lucide-react';
import { aiAssistantApi, bankingApi, DEFAULT_TRANSFER_OTP } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { copyToClipboard } from '../utils/clipboard';
import { formatHumanReadableError } from '../utils/formatError';




export const AiAssistant = ({ isOpen, onClose, onTransferSuccess, externalPrompt }) => {
  const { user, refreshAccount } = useAuth();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello ${user?.full_name?.split(' ')[0] || 'there'}. I am **Tirenn**, your financial intelligence co-pilot.\n\nI have direct access to your banking core and knowledge base. How can I assist you today?`,
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [apiKey, setApiKey] = useState(sessionStorage.getItem('openrouter_key') || '');
  const [model, setModel] = useState(sessionStorage.getItem('openrouter_model') || '');

  const [availableModels, setAvailableModels] = useState([]);
  const [executingTransfer, setExecutingTransfer] = useState(false);
  const [copiedMessageIdx, setCopiedMessageIdx] = useState(null);

  const [transferStatus, setTransferStatus] = useState({});
  const [transferOtp, setTransferOtp] = useState({});

  const messagesEndRef = useRef(null);



  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await aiAssistantApi.getAvailableModels();
        if (data?.models && data.models.length > 0) {
          setAvailableModels(data.models);
          const savedModel = sessionStorage.getItem('openrouter_model');
          if (!savedModel) {
            const chosen = data.default_model || data.models[0];
            setModel(chosen);
          } else {
            setModel(savedModel);
          }
        }
      } catch (err) {
        console.warn('Failed to load dynamic model list from backend:', err);
      }
    };
    fetchModels();
  }, []);



  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);


  useEffect(() => {
    if (externalPrompt) {
      handleSend(externalPrompt);
    }
  }, [externalPrompt]);


  const handleSend = async (userText) => {
    const textToSend = (userText || input).trim();
    if (!textToSend || loading) return;

    const newMessages = [...messages, { role: 'user', content: textToSend }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const payloadMessages = newMessages.map((m) => ({ role: m.role, content: m.content }));
      const currentApiKey = sessionStorage.getItem('openrouter_key') || '';
      const currentModel = sessionStorage.getItem('openrouter_model') || model;
      const res = await aiAssistantApi.sendChat(payloadMessages, currentApiKey, currentModel);


      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: res.reply,
          action_type: res.action_type,
          action_data: res.action_data,
          tools_used: res.tools_used,
        },
      ]);

      if (res.action_type === 'SHOW_NEW_ACCOUNT' || res.action_type === 'SHOW_ACCOUNTS') {
        await refreshAccount();
      }

    } catch (err) {
      console.error('AI Chat Error:', err);
      const serverDetail = formatHumanReadableError(err, 'Unable to reach Tirenn AI microservice. Ensure Python backend is active.');
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `⚠️ **AI Service Notice:** ${serverDetail}`,
        },
      ]);

    } finally {
      setLoading(false);
    }
  };


  const handleConfirmTransfer = async (draft, msgIndex) => {
    const otpToUse = String(transferOtp[msgIndex] || '').trim();
    if (!otpToUse || otpToUse.length !== 6) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Transfer Authorization Failed:** Please enter the 6-digit confirmation OTP code into the card above before dispatching.`,
        },
      ]);
      return;
    }

    setExecutingTransfer(true);
    try {
      await bankingApi.transfer(
        draft.to_account_number,
        draft.amount_dollars,
        draft.description,
        draft.category || 'Transfer',
        otpToUse,
        draft.from_account_id
      );
      setTransferStatus((prev) => ({ ...prev, [msgIndex]: 'SUCCESS' }));
      await refreshAccount();
      if (onTransferSuccess) onTransferSuccess();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `✅ **Transfer Dispatched Successfully**\n\nSent **$${draft.amount_dollars.toFixed(2)}** to **${draft.recipient_name}** (${draft.to_account_number}). Your balance has been updated.`,
        },
      ]);
    } catch (err) {
      setTransferStatus((prev) => ({ ...prev, [msgIndex]: 'ERROR' }));
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Transfer Failed:** ${formatHumanReadableError(err, 'Execution halted. Please check your inputs and try again.')}`,
        },
      ]);
    } finally {
      setExecutingTransfer(false);
    }
  };



  const handleResetSession = async () => {
    if (resetting || loading) return;
    setResetting(true);
    try {
      await aiAssistantApi.resetSession();
      setMessages([
        {
          role: 'assistant',
          content: `🔄 **Conversation Context Cleared**\n\nHello ${user?.full_name?.split(' ')[0] || 'there'}. I am **Tirenn**, your financial intelligence co-pilot. How can I assist you today?`,
        },
      ]);
      setTransferStatus({});
    } catch (err) {
      console.error('Failed to reset AI conversation session:', err);
    } finally {
      setResetting(false);
    }
  };

  const quickChips = [
    'Check my balance',
    'Open a new savings account (Vacation Savings)',
    'Show all my bank accounts',
    'Freeze my debit card',
    'Convert $500 USD to IDR',
    'Calculate loan: $35,000 for 5 years at 6.5%',
    'Show my saved beneficiaries',
    'Set daily transfer limit to $8,000',
    'Show my profile & KYC status',
    'Generate my monthly account statement',
    'Monthly spending breakdown',
    'Transfer $50 to Sarah Smith (ACC-83920194)',
  ];





  if (!isOpen) return null;

  return (
    <>
      {/* Mobile Backdrop to prevent background touches and dismiss chat on tap outside */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm sm:hidden transition-opacity"
      />

      <div className="fixed inset-x-0 bottom-0 top-0 sm:top-auto sm:inset-auto sm:bottom-4 sm:right-4 z-50 w-full sm:w-[460px] h-[100dvh] sm:h-[660px] sm:max-h-[90vh] bg-[#0c0d12] border-t sm:border border-white/[0.12] rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col overflow-hidden overscroll-contain animate-fadeIn">
        
        {/* Header */}
        <div className="p-4 bg-[#11131a] border-b border-white/[0.08] flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <h3 className="font-semibold text-xs text-white">Tirenn Financial Intelligence</h3>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </div>

              <p className="text-[10px] text-slate-500 font-mono">Tool calling • ChromaDB vector RAG</p>
            </div>
          </div>


        <div className="flex items-center space-x-1">
          <button
            onClick={handleResetSession}
            disabled={resetting || loading}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors ${resetting ? 'animate-spin text-rose-400' : ''}`}
            title="Reset Conversation (Clear Redis History)"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>


      {/* Messages Scroll Area */}
      <div 
        className="flex-1 overflow-y-auto p-4 space-y-3.5 overscroll-y-contain touch-pan-y"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >

        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div key={idx} className={`flex items-start space-x-2.5 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div
                className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 text-xs ${
                  isUser
                    ? 'bg-white/[0.1] text-slate-200'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}
              >
                {isUser ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
              </div>

              <div className={`max-w-[85%] space-y-2`}>
                <div
                  className={`p-3.5 rounded-xl text-xs leading-relaxed ${
                    isUser
                      ? 'bg-emerald-500 text-slate-950 font-medium whitespace-pre-wrap'
                      : 'bg-[#14161f] text-slate-200 border border-white/[0.06]'
                  }`}
                >
                  {isUser ? (
                    msg.content
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ node, ...props }) => (
                          <div className="my-2.5 overflow-x-auto rounded-lg border border-white/[0.08] bg-black/40">
                            <table className="w-full text-left border-collapse text-[11px] font-mono" {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => (
                          <thead className="bg-white/[0.06] text-slate-200 border-b border-white/[0.08]" {...props} />
                        ),
                        tbody: ({ node, ...props }) => (
                          <tbody className="divide-y divide-white/[0.04]" {...props} />
                        ),
                        tr: ({ node, ...props }) => (
                          <tr className="hover:bg-white/[0.02] transition-colors" {...props} />
                        ),
                        th: ({ node, ...props }) => (
                          <th className="p-2 font-semibold text-emerald-400 text-[10px] uppercase tracking-wider" {...props} />
                        ),
                        td: ({ node, ...props }) => (
                          <td className="p-2 text-slate-300" {...props} />
                        ),
                        strong: ({ node, ...props }) => (
                          <strong className="font-bold text-white" {...props} />
                        ),
                        em: ({ node, ...props }) => (
                          <em className="italic text-slate-200" {...props} />
                        ),
                        p: ({ node, ...props }) => (
                          <p className="mb-2 last:mb-0 leading-relaxed" {...props} />
                        ),
                        ul: ({ node, ...props }) => (
                          <ul className="list-disc list-inside space-y-1 my-1.5 text-slate-300" {...props} />
                        ),
                        ol: ({ node, ...props }) => (
                          <ol className="list-decimal list-inside space-y-1 my-1.5 text-slate-300" {...props} />
                        ),
                        li: ({ node, ...props }) => (
                          <li className="text-slate-300" {...props} />
                        ),
                        code: ({ node, inline, ...props }) => (
                          <code
                            className="px-1.5 py-0.5 rounded bg-black/50 text-emerald-400 font-mono text-[11px] border border-white/[0.06]"
                            {...props}
                          />
                        ),
                        pre: ({ node, ...props }) => (
                          <pre
                            className="p-2.5 rounded-lg bg-black/60 border border-white/[0.08] overflow-x-auto my-2 text-[11px] font-mono text-emerald-300"
                            {...props}
                          />
                        ),
                        blockquote: ({ node, ...props }) => (
                          <blockquote
                            className="border-l-2 border-emerald-500/60 pl-2.5 my-2 text-slate-400 italic"
                            {...props}
                          />
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>

                  )}

                  {!isUser && (
                    <div className="flex items-center justify-end pt-1.5 mt-1 border-t border-white/[0.04]">
                      <button
                        onClick={async () => {
                          const ok = await copyToClipboard(msg.content);
                          if (ok) {
                            setCopiedMessageIdx(idx);
                            setTimeout(() => setCopiedMessageIdx(null), 2000);
                          }
                        }}
                        className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center space-x-1 transition-colors cursor-pointer"
                        title="Copy message"
                      >
                        {copiedMessageIdx === idx ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-400" />
                            <span className="text-emerald-400 text-[10px]">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>


                {/* Tool Tracing Pills */}
                {msg.tools_used && msg.tools_used.length > 0 && (
                  <div className="flex items-center space-x-1 text-[10px] text-slate-500">
                    <span>invoked:</span>
                    {msg.tools_used.map((t) => (
                      <span key={t} className="px-1.5 py-0.2 rounded bg-white/[0.04] text-slate-400 font-mono text-[10px]">
                        {t}
                      </span>
                    ))}
                  </div>
                )}

                {/* New Bank Account & Card Issued Card */}
                {msg.action_type === 'SHOW_NEW_ACCOUNT' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-950/40 via-black to-[#10141f] border border-emerald-500/40 space-y-3 shadow-xl text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="p-1 rounded bg-emerald-500/20 text-emerald-400">💳</span>
                        <span className="font-semibold text-emerald-300">{msg.action_data.account_name}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[10px] font-bold border border-emerald-500/30">
                        {msg.action_data.account_type}
                      </span>
                    </div>

                    {/* Virtual Card Preview inside Chat */}
                    <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.08] space-y-2 font-mono text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-[9px] uppercase tracking-wider">{msg.action_data.card_brand} DEBIT</span>
                        <span className="text-emerald-400 font-bold">{msg.action_data.status}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm tracking-widest text-slate-100 font-semibold">
                        <span>{msg.action_data.card_number}</span>
                        <button
                          onClick={() => copyToClipboard(msg.action_data.card_number)}
                          className="p-1 rounded text-slate-400 hover:text-white cursor-pointer"
                          title="Copy card number"
                        >
                          <Copy className="h-3 w-3" />
                        </button>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-white/[0.06]">
                        <span>Exp: <strong className="text-slate-200">{msg.action_data.card_expiry}</strong></span>
                        <span>CVV: <strong className="text-slate-200">{msg.action_data.card_cvv}</strong></span>
                        <span>Bal: <strong className="text-emerald-400">${(msg.action_data.balance_dollars || 0).toFixed(2)}</strong></span>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 flex items-center justify-between">
                      <span>Account: <strong className="text-slate-300 font-mono">{msg.action_data.account_number}</strong></span>
                      <span className="text-emerald-400 font-medium">Added to your portfolio</span>
                    </div>
                  </div>
                )}


                {/* All Accounts Summary Card */}
                {msg.action_type === 'SHOW_ACCOUNTS' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2.5 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Your Bank Accounts</span>
                      <span className="text-[10px] font-mono text-emerald-400">{msg.action_data.count} Accounts</span>
                    </div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {(msg.action_data.accounts || []).map((acc) => (
                        <div key={acc.id} className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
                          <div>
                            <div className="font-medium text-slate-200">{acc.account_name || 'Account'}</div>
                            <div className="text-[10px] text-slate-400 font-mono">{acc.account_number} • {acc.card_brand || 'VISA'} • {acc.card_number ? `${acc.card_number.slice(0, 4)}...${acc.card_number.slice(-4)}` : ''}</div>
                          </div>
                          <div className="font-mono text-xs font-semibold text-emerald-400">
                            ${((acc.balance_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Interactive Transfer Confirmation Card */}
                {msg.action_type === 'CONFIRM_TRANSFER' && msg.action_data && (

                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2.5 shadow-md">
                    <div className="flex items-center justify-between text-xs font-medium text-slate-200">
                      <span className="text-emerald-400 font-mono">Transfer Authorization Draft</span>
                      <span className="font-mono text-emerald-400 font-semibold text-sm">
                        ${msg.action_data.amount_dollars.toFixed(2)}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-1 bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04]">
                      <div>Recipient: <strong className="text-slate-200">{msg.action_data.recipient_name}</strong></div>
                      <div>Account: <span className="font-mono text-slate-300">{msg.action_data.to_account_number}</span></div>
                      <div>Note: <span className="text-slate-300">{msg.action_data.description}</span></div>
                    </div>

                    {/* Confirmation OTP Gate Field */}
                    <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center space-x-1 text-amber-400 font-semibold">
                          <ShieldCheck className="h-3 w-3" />
                          <span>Confirmation OTP</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setTransferOtp((prev) => ({ ...prev, [idx]: DEFAULT_TRANSFER_OTP }))}
                          className="text-[10px] text-amber-300 underline font-mono cursor-pointer hover:text-amber-200"
                        >
                          Auto ({DEFAULT_TRANSFER_OTP})
                        </button>
                      </div>
                      <input
                        type="text"
                        maxLength={6}
                        value={transferOtp[idx] || ''}
                        onChange={(e) => setTransferOtp((prev) => ({ ...prev, [idx]: e.target.value }))}
                        placeholder="Enter 6-digit OTP"
                        className="w-full px-2 py-1 bg-black/50 border border-amber-500/30 rounded text-amber-200 text-xs font-mono tracking-widest text-center focus:outline-none focus:border-amber-400"
                      />
                    </div>

                    {transferStatus[idx] === 'SUCCESS' ? (
                      <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs font-medium flex items-center justify-center space-x-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Execution Complete</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleConfirmTransfer(msg.action_data, idx)}
                        disabled={executingTransfer}
                        className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs flex items-center justify-center space-x-1.5 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <span>{executingTransfer ? 'Transacting...' : 'Authorize & Dispatch Transfer'}</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                )}

                {/* Profile & KYC Card */}
                {msg.action_type === 'SHOW_PROFILE' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{msg.action_data.full_name}</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[10px] font-semibold border border-emerald-500/30">
                        KYC: {msg.action_data.kyc_status || 'VERIFIED'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 space-y-1 bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04]">
                      <div>Address: <span className="text-slate-200">{msg.action_data.address_street}, {msg.action_data.address_city}, {msg.action_data.address_state} {msg.action_data.address_postal_code}, {msg.action_data.address_country}</span></div>
                      <div>Document: <span className="text-slate-200 font-mono">{msg.action_data.kyc_doc_type} ({msg.action_data.kyc_doc_number})</span></div>
                      <div>Contact: <span className="text-slate-300 font-mono">{msg.action_data.phone_number || msg.action_data.email}</span></div>
                    </div>
                  </div>
                )}

                {/* Statement Report Card */}
                {msg.action_type === 'SHOW_STATEMENT' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2.5 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Account Statement</span>
                      <span className="text-[10px] font-mono text-emerald-400">{msg.action_data.statement_id}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04] font-mono">
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">Starting Balance</span>
                        <span className="text-slate-200">${((msg.action_data.starting_balance_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">Ending Balance</span>
                        <span className="text-emerald-400 font-semibold">${((msg.action_data.ending_balance_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">Total Inflow (+)</span>
                        <span className="text-emerald-300">+${((msg.action_data.total_deposits_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">Total Outflow (-)</span>
                        <span className="text-rose-300">-${((msg.action_data.total_withdrawals_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      Period: {String(msg.action_data.period_start || '').substring(0, 10)} to {String(msg.action_data.period_end || '').substring(0, 10)} • {msg.action_data.transaction_count} transactions
                    </div>
                  </div>
                )}

                {/* Transaction Detail Card */}
                {msg.action_type === 'SHOW_TRANSACTION_DETAIL' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2 shadow-md text-xs">
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-slate-400 text-[10px]">{msg.action_data.reference_number}</span>
                      <span className="font-semibold text-emerald-400 text-sm">
                        ${((msg.action_data.amount_cents || 0) / 100).toFixed(2)}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 space-y-1 bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04]">
                      <div>Description: <strong className="text-slate-100">{msg.action_data.description || msg.action_data.type}</strong></div>
                      <div>Category: <span className="text-slate-200">{msg.action_data.category}</span></div>
                      {msg.action_data.counterparty_name && (
                        <div>Counterparty: <span className="text-slate-200">{msg.action_data.counterparty_name} ({msg.action_data.counterparty_account_num})</span></div>
                      )}
                      <div className="text-[10px] text-slate-500 font-mono">{msg.action_data.created_at}</div>
                    </div>
                  </div>
                )}

                {/* Card Lock / Security Card */}
                {msg.action_type === 'SHOW_LOCK_STATUS' && msg.action_data && (
                  <div className={`p-3.5 rounded-xl bg-black/60 border space-y-2 shadow-md text-xs ${msg.action_data.is_frozen ? 'border-rose-500/40' : 'border-emerald-500/40'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Security Control Status</span>
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${msg.action_data.is_frozen ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'}`}>
                        {msg.action_data.is_frozen ? '🔒 Card Frozen' : '🟢 Card Active'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04]">
                      {msg.action_data.is_frozen ? 'All outgoing card transactions and wire transfers are temporarily blocked.' : 'Normal banking and fund transfer operations are enabled.'}
                    </div>
                  </div>
                )}

                {/* Forex Conversion Card */}
                {msg.action_type === 'SHOW_FOREX' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2 shadow-md text-xs font-mono">
                    <div className="flex items-center justify-between text-slate-200">
                      <span>{msg.action_data.from} ➔ {msg.action_data.to}</span>
                      <span className="text-emerald-400 font-bold text-sm">
                        {msg.action_data.converted_amount.toLocaleString()} {msg.action_data.to}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 bg-white/[0.02] p-2 rounded-lg border border-white/[0.04] space-y-0.5">
                      <div>Rate: 1 {msg.action_data.from} = {msg.action_data.exchange_rate} {msg.action_data.to}</div>
                      <div>Spread Fee: {msg.action_data.spread_fee_pct}% (~${msg.action_data.estimated_fee_usd.toFixed(2)} USD)</div>
                    </div>
                  </div>
                )}

                {/* Loan & Mortgage Simulation Card */}
                {msg.action_type === 'SHOW_LOAN_CALC' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{msg.action_data.loan_type} Financing Simulation</span>
                      <span className="text-emerald-400 font-mono font-bold text-sm">${msg.action_data.monthly_payment.toFixed(2)}/mo</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-white/[0.02] p-2.5 rounded-lg border border-white/[0.04]">
                      <div>
                        <span className="text-slate-500 block text-[9px]">PRINCIPAL</span>
                        <span className="text-slate-200">${msg.action_data.principal.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px]">DURATION</span>
                        <span className="text-slate-200">{msg.action_data.term_months} mos</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px]">TOTAL INTEREST</span>
                        <span className="text-amber-300">${msg.action_data.total_interest.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px]">TOTAL REPAYMENT</span>
                        <span className="text-emerald-400">${msg.action_data.total_payment.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Saved Payees / Beneficiaries Card */}
                {msg.action_type === 'SHOW_BENEFICIARIES' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-2 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Trusted Beneficiaries</span>
                      <span className="text-[10px] text-slate-400 font-mono">{(msg.action_data.beneficiaries || []).length} Contacts</span>
                    </div>
                    <div className="space-y-1.5 max-h-36 overflow-y-auto">
                      {(msg.action_data.beneficiaries || []).map((b, bi) => (
                        <div key={bi} className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04] flex items-center justify-between">
                          <div>
                            <div className="font-medium text-slate-200">{b.nickname}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{b.account_number} • {b.bank_name}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Spending Limits Card */}
                {msg.action_type === 'SHOW_LIMITS' && msg.action_data && (
                  <div className="p-3.5 rounded-xl bg-black/60 border border-emerald-500/30 space-y-1.5 shadow-md text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Account Transfer Limit</span>
                      <span className="font-mono text-emerald-400 font-bold text-sm">
                        ${((msg.action_data.daily_transfer_limit_cents || 0) / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400">Daily maximum outgoing transaction quota updated in banking core.</div>
                  </div>
                )}
              </div>
            </div>
          );
        })}



        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs pl-8 font-mono">
            <RefreshCw className="h-3 w-3 animate-spin text-emerald-400" />
            <span>Consulting banking tools & knowledge store...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div 
        className="px-3 py-2 border-t border-white/[0.06] bg-black/40 overflow-x-auto overscroll-x-contain touch-pan-x flex-shrink-0 flex items-center space-x-1.5"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {quickChips.map((chip, i) => (
          <button
            key={i}
            onClick={() => handleSend(chip)}
            className="px-2.5 py-1 rounded-md bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 text-[10px] whitespace-nowrap transition-colors flex-shrink-0 cursor-pointer border border-white/[0.06]"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="p-3 bg-[#11131a] border-t border-white/[0.08] flex-shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a financial instruction or query..."
            className="flex-1 px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium transition-all disabled:opacity-40 cursor-pointer"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>

    </div>
    </>
  );
};

