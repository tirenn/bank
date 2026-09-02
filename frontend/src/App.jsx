import React, { useState, useEffect } from 'react';

import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { AccountCard } from './components/AccountCard';
import { QuickActions } from './components/QuickActions';
import { TransactionList } from './components/TransactionList';
import { SpendingAnalytics } from './components/SpendingAnalytics';
import { TransferModal } from './components/TransferModal';
import { DepositModal } from './components/DepositModal';
import { AiAssistant } from './components/AiAssistant';
import { AdminRagDashboard } from './components/AdminRagDashboard';
import { Sparkles } from 'lucide-react';

function DashboardContent() {
  const { user, isAdmin, loading } = useAuth();
  const [isTransferOpen, setIsTransferOpen] = useState(false);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [isAiChatOpen, setIsAiChatOpen] = useState(false);
  const [aiExternalPrompt, setAiExternalPrompt] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleTriggerRefresh = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleAiPrompt = (promptText) => {
    setAiExternalPrompt(promptText);
    setIsAiChatOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#08090d] flex items-center justify-center text-slate-500 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span>INITIALIZING AURA SECURE TERMINAL...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthModal />;
  }

  return (
    <div className="min-h-screen bg-[#08090d] text-slate-100 flex flex-col relative">
      <Navbar
        onOpenAiChat={() => setIsAiChatOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-7 space-y-7">
        
        {/* VIEW 1: ADMIN RAG DASHBOARD (Admin accounts do not have customer bank accounts) */}
        {isAdmin ? (
          <AdminRagDashboard />
        ) : (
          /* VIEW 2: CUSTOMER BANKING DASHBOARD */
          <>
            {/* Top Header Row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-white">
                  Overview
                </h1>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Liquidity balance & transaction stream for {user.full_name}
                </p>
              </div>

              <button
                onClick={() => setIsAiChatOpen(true)}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 hover:text-white text-xs font-medium w-fit cursor-pointer transition-all"
              >
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                <span>Open Nova Financial Assistant</span>
              </button>
            </div>

            {/* Top Section: Account Overview & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7">
                <AccountCard
                  onTransferClick={() => setIsTransferOpen(true)}
                  onDepositClick={() => setIsDepositOpen(true)}
                />
              </div>

              <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
                <QuickActions
                  onTransfer={() => setIsTransferOpen(true)}
                  onDeposit={() => setIsDepositOpen(true)}
                  onAiPrompt={handleAiPrompt}
                />

                <div className="p-4 rounded-2xl bg-[#0f1117] border border-white/[0.08] flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-xs font-medium text-slate-200">High-Yield Treasury Reserve</div>
                    <div className="text-[11px] text-slate-500 font-mono">4.75% APY • Daily interest compounding</div>
                  </div>
                  <button
                    onClick={() => handleAiPrompt('Explain the 4.75% APY High-Yield Savings terms and withdrawal policy')}
                    className="text-xs text-emerald-400 hover:text-emerald-300 font-medium cursor-pointer"
                  >
                    Inquire →
                  </button>
                </div>
              </div>
            </div>

            {/* Ledger & Cash Flow Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Main Transaction List */}
              <div className="lg:col-span-7">
                <TransactionList refreshTrigger={refreshTrigger} />
              </div>

              {/* Monthly Cash Flow Analytics */}
              <div className="lg:col-span-5">
                <SpendingAnalytics refreshTrigger={refreshTrigger} />
              </div>
            </div>
          </>
        )}

      </main>

      {/* Floating Action Button for Nova AI */}
      {!isAiChatOpen && (
        <button
          onClick={() => setIsAiChatOpen(true)}
          className="fixed bottom-5 right-5 z-40 px-3.5 py-2.5 rounded-xl bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.12] text-slate-100 text-xs font-medium shadow-xl hover:scale-[1.02] transition-all flex items-center space-x-2 cursor-pointer backdrop-blur-md"
        >
          <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
          <span>Nova Copilot</span>
        </button>
      )}

      {/* Customer Modals (Only applicable for non-admin customer roles) */}
      {!isAdmin && (
        <>
          <TransferModal
            isOpen={isTransferOpen}
            onClose={() => setIsTransferOpen(false)}
            onSuccess={handleTriggerRefresh}
          />

          <DepositModal
            isOpen={isDepositOpen}
            onClose={() => setIsDepositOpen(false)}
            onSuccess={handleTriggerRefresh}
          />
        </>
      )}

      <AiAssistant
        isOpen={isAiChatOpen}
        onClose={() => {
          setIsAiChatOpen(false);
          setAiExternalPrompt('');
        }}
        onTransferSuccess={handleTriggerRefresh}
        externalPrompt={aiExternalPrompt}
      />
    </div>
  );
}


export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}

