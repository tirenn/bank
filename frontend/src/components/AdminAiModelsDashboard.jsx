import React, { useState, useEffect } from 'react';
import {
  Key,
  Eye,
  EyeOff,
  Sparkles,
  RefreshCw,
  AlertCircle,
  RotateCcw,
  Layers,
  Lock
} from 'lucide-react';
import { adminModelApi } from '../services/api';

export const AdminAiModelsDashboard = () => {
  // Session-only Storage State for Dedicated Paid Models (Free-text input)
  const [openRouterApiKey, setOpenRouterApiKey] = useState(sessionStorage.getItem('openrouter_key') || '');
  const [paidModelSlug, setPaidModelSlug] = useState(sessionStorage.getItem('openrouter_model') || '');
  const [showApiKey, setShowApiKey] = useState(false);
  const [actionStatus, setActionStatus] = useState(null);

  // PostgreSQL AI Models Database State (Read-Only Free Tier Pool)
  const [dbModels, setDbModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);

  const fetchDbModels = async () => {
    setLoadingModels(true);
    try {
      const data = await adminModelApi.listModels();
      setDbModels(data.models || []);
    } catch (e) {
      console.error('Failed to load DB models:', e);
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    fetchDbModels();
  }, []);

  const handleActivatePaidModel = (e) => {
    e.preventDefault();
    const cleanKey = openRouterApiKey.trim();
    const cleanModel = paidModelSlug.trim();

    if (!cleanKey) {
      setActionStatus({
        success: false,
        message: '❌ OpenRouter API Key is required to activate Dedicated Paid Mode.'
      });
      return;
    }

    if (!cleanModel) {
      setActionStatus({
        success: false,
        message: '❌ Paid Model Slug is required when an OpenRouter API Key is provided.'
      });
      return;
    }

    // Prohibit free model slugs in paid override
    if (cleanModel.toLowerCase().endsWith(':free')) {
      setActionStatus({
        success: false,
        message: '⚠️ Free models (:free) cannot be used as a Primary Paid Model. Please use Free Tier Mode below for free models.'
      });
      return;
    }

    // Save strictly to browser sessionStorage
    sessionStorage.setItem('openrouter_key', cleanKey);
    sessionStorage.setItem('openrouter_model', cleanModel);

    setActionStatus({
      success: true,
      message: `🎯 Dedicated Paid Mode ACTIVE: Strictly using model '${cleanModel}' (Fallback Disabled). Saved to sessionStorage.`
    });
    setTimeout(() => setActionStatus(null), 5000);
  };

  const handleResetToFreePool = () => {
    sessionStorage.removeItem('openrouter_key');
    sessionStorage.removeItem('openrouter_model');
    setOpenRouterApiKey('');
    setPaidModelSlug('');
    setActionStatus({
      success: true,
      message: '🔄 Switched to Free Tier Mode! The system is now using the system-provisioned free model pool with Automatic Fallback.'
    });
    setTimeout(() => setActionStatus(null), 5000);
  };

  const isPaidModeActive = Boolean(sessionStorage.getItem('openrouter_key') && sessionStorage.getItem('openrouter_model'));
  const activeSessionModel = sessionStorage.getItem('openrouter_model');

  return (
    <div className="space-y-7 animate-fadeIn">
      
      {/* Header Banner */}
      <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px] font-semibold">
                AI ORCHESTRATION CONSOLE
              </span>
              <span className="text-xs text-slate-500 font-mono">•</span>
              <span className="text-xs text-slate-400 font-mono">Dual-Mode Routing Engine</span>
            </div>
            <h2 className="text-lg font-semibold text-white">AI Model & Fallback Management</h2>
            <p className="text-xs text-slate-400 font-mono">
              Dedicated Paid Model configuration • System-Provisioned Free Tier fallback pool (Read-Only)
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-medium text-slate-200">Active Routing Status</div>
              <div className="text-[11px] text-emerald-400 font-mono font-semibold">
                {isPaidModeActive ? '🎯 DEDICATED PAID MODE' : '⚡ FREE TIER CASCADE'}
              </div>
            </div>
            <button
              onClick={fetchDbModels}
              className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 border border-white/[0.06] transition-colors cursor-pointer"
              title="Refresh Models"
            >
              <RefreshCw className={`h-4 w-4 ${loadingModels ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Security & Ephemeral Session Storage Warning */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start space-x-3">
        <AlertCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-amber-200">
            🔒 Security & Session Storage Notice (Ephemeral)
          </p>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Your <strong>OpenRouter API Key</strong> and <strong>Paid Model Slug</strong> are stored securely in browser memory (<code className="text-amber-400 bg-black/40 px-1.5 py-0.5 rounded font-mono">sessionStorage</code>) and <strong>will be automatically deleted when this tab or browser window is closed</strong>.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 text-[11px] text-slate-400">
            <div className="p-2 rounded-lg bg-black/30 border border-white/[0.04]">
              <span className="text-emerald-400 font-semibold font-mono">⚡ Free Tier Mode (Default):</span> Uses the system-provisioned free model pool with <em>Automatic Cascading Fallback</em> upon rate limits (HTTP 429).
            </div>
            <div className="p-2 rounded-lg bg-black/30 border border-white/[0.04]">
              <span className="text-amber-400 font-semibold font-mono">🎯 Dedicated Paid Mode:</span> Requires an API Key + Model Slug. Strictly locks to your specified model with <em>Fallback DISABLED</em>.
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 1: UNIFIED DEDICATED PAID MODEL CONFIGURATION (FREE TEXT INPUT) */}
      <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-3">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Key className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Dedicated Paid Model Configuration</h3>
              <p className="text-[11px] text-slate-400 font-mono">Configure custom API Key & primary paid model slug (No Fallback)</p>
            </div>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-mono font-semibold border flex items-center space-x-1.5 w-fit ${
              isPaidModeActive
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <div className={`w-2 h-2 rounded-full ${isPaidModeActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            <span>{isPaidModeActive ? `PAID ACTIVE: ${activeSessionModel}` : 'FREE TIER ACTIVE'}</span>
          </span>
        </div>

        {actionStatus && (
          <div
            className={`p-3 rounded-xl border text-xs ${
              actionStatus.success
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}
          >
            {actionStatus.message}
          </div>
        )}

        {/* Unified Form: API Key + Direct Free-Text Paid Model Slug */}
        <form onSubmit={handleActivatePaidModel} className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            
            {/* Field 1: OpenRouter API Key */}
            <div className="lg:col-span-6 space-y-1.5 text-xs">
              <label className="block font-medium text-slate-300">
                1. OpenRouter API Key <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={openRouterApiKey}
                  onChange={(e) => setOpenRouterApiKey(e.target.value)}
                  placeholder="sk-or-v1-..."
                  className="w-full pl-3 pr-10 py-2.5 bg-black/50 border border-white/[0.08] rounded-xl text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500/60 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-[10px] text-slate-500">
                Required to authenticate and route chat queries through your OpenRouter account.
              </p>
            </div>

            {/* Field 2: Direct Free-Text Paid Model Slug */}
            <div className="lg:col-span-6 space-y-1.5 text-xs">
              <label className="block font-medium text-slate-300">
                2. Paid Model Slug / Identifier <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={paidModelSlug}
                onChange={(e) => setPaidModelSlug(e.target.value)}
                placeholder="e.g. anthropic/claude-3.5-sonnet, openai/gpt-4o, deepseek/deepseek-chat"
                className="w-full px-3 py-2.5 bg-black/50 border border-white/[0.08] rounded-xl text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500/60 font-mono text-xs"
              />
              <p className="text-[10px] text-slate-500">
                Enter any official OpenRouter model slug. Model availability and quota are verified live by OpenRouter.
              </p>
            </div>

          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-3 pt-2">
            <button
              type="submit"
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition-all shadow-md cursor-pointer flex items-center justify-center space-x-2"
            >
              <Sparkles className="h-4 w-4" />
              <span>Activate Dedicated Paid Model</span>
            </button>

            {isPaidModeActive && (
              <button
                type="button"
                onClick={handleResetToFreePool}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-rose-500/20 text-slate-300 hover:text-rose-400 border border-white/[0.08] font-medium text-xs transition-colors cursor-pointer flex items-center justify-center space-x-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset to Free Tier Pool</span>
              </button>
            )}
          </div>
        </form>
      </div>

      {/* SECTION 2: SYSTEM-PROVISIONED FREE TIER FALLBACK POOL (READ-ONLY) */}
      <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-white/[0.06] gap-2">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Layers className="h-4 w-4 text-emerald-400" />
              <span>System-Provisioned Free Tier Fallback Pool (Read-Only)</span>
            </h3>
            <p className="text-[11px] text-slate-500 font-mono">
              Orchestrated automatically by the core banking engine • Cascading execution order (Priority #1 ➔ #2 ➔ #3)
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[10px] font-bold flex items-center space-x-1">
              <Lock className="h-3 w-3" />
              <span>IMMUTABLE SYSTEM POOL</span>
            </span>
            <span className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-slate-300 font-mono text-[10px]">
              {dbModels.filter(m => m.is_free).length} ACTIVE FREE MODELS
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-white/[0.06] text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Fallback Priority</th>
                <th className="py-2.5 px-3">Model Name</th>
                <th className="py-2.5 px-3">OpenRouter Slug</th>
                <th className="py-2.5 px-3">Tier</th>
                <th className="py-2.5 px-3">Execution Strategy</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {loadingModels ? (
                <tr>
                  <td colSpan="6" className="py-10 text-center text-slate-500 font-mono">
                    Loading system AI models from PostgreSQL...
                  </td>
                </tr>
              ) : dbModels.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-10 text-center text-slate-500">
                    No free models registered in database.
                  </td>
                </tr>
              ) : (
                dbModels.map((m, idx) => (
                  <tr key={m.id || idx} className="hover:bg-white/[0.02] transition-colors font-mono text-xs">
                    <td className="py-3 px-3">
                      <span className="px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold">
                        #{m.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-sans font-medium text-slate-200 whitespace-nowrap">
                      {m.name}
                    </td>
                    <td className="py-3 px-3 text-[11px] text-slate-400 whitespace-nowrap">
                      {m.model_id}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        FREE
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[11px] text-slate-400 font-sans whitespace-nowrap">
                      {m.priority === 1 ? '🎯 Primary Free Target' : `🔄 Fallback #${m.priority} on HTTP 429`}
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        SYSTEM ACTIVE
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="p-3 rounded-xl bg-black/30 border border-white/[0.04] text-[11px] text-slate-400 flex items-center justify-between">
          <span>ℹ️ Free models are immutable and managed directly by the banking core to guarantee continuous high service availability.</span>
          <span className="font-mono text-emerald-400 text-[10px]">Zero Maintenance Required</span>
        </div>
      </div>

    </div>
  );
};
