import React, { useState } from 'react';
import { Landmark, LogOut, Sparkles, Menu, X, Database, CreditCard } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar = ({ onOpenAiChat, currentView = 'banking', onViewChange }) => {
  const { user, isAdmin, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="border-b border-white/[0.08] bg-[#0c0d12]/95 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Desktop Nav */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-white/[0.06] border border-white/[0.1] flex items-center justify-center text-white">
              <Landmark className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-semibold tracking-tight text-white">
                AURA
              </span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {isAdmin ? 'ADMIN' : 'CORE'}
              </span>
            </div>
          </div>

          {/* Admin Navigation Selector (Desktop) */}
          {isAdmin && (
            <div className="hidden md:flex items-center space-x-1 p-1 rounded-lg bg-black/40 border border-white/[0.06] text-xs">
              <button
                onClick={() => onViewChange && onViewChange('banking')}
                className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer flex items-center space-x-1.5 ${
                  currentView === 'banking'
                    ? 'bg-white text-slate-950 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CreditCard className="h-3 w-3" />
                <span>Banking View</span>
              </button>
              <button
                onClick={() => onViewChange && onViewChange('admin')}
                className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer flex items-center space-x-1.5 ${
                  currentView === 'admin'
                    ? 'bg-emerald-500 text-slate-950 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Database className="h-3 w-3" />
                <span>RAG Management</span>
              </button>
            </div>
          )}
        </div>

        {/* Right Nav actions */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          <button
            onClick={onOpenAiChat}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.08] border border-white/[0.1] text-slate-200 hover:text-white transition-all text-xs font-medium cursor-pointer"
          >
            <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
            <span className="hidden xs:inline sm:inline">Nova Copilot</span>
          </button>

          {user && (
            <div className="flex items-center space-x-2 sm:space-x-3 sm:pl-3 sm:border-l sm:border-white/[0.08]">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-medium text-slate-200">{user.full_name}</span>
                <span className="text-[10px] text-slate-400 font-mono truncate max-w-[140px]">
                  {user.email}
                </span>
              </div>
              
              <div className="h-8 w-8 rounded-full bg-white/[0.08] border border-white/[0.12] flex items-center justify-center text-slate-200 font-medium text-xs">
                {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>

              <button
                onClick={logout}
                title="Sign out"
                className="hidden sm:flex p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>

              {/* Mobile Menu Hamburger Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-colors"
                aria-label="Toggle navigation menu"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          )}
        </div>

      </div>

      {/* Mobile Menu Dropdown Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden px-4 pt-2 pb-4 border-t border-white/[0.08] bg-[#0f1117] space-y-3 animate-fadeIn">
          {user && (
            <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] flex items-center justify-between">
              <div>
                <div className="text-xs font-medium text-slate-200">{user.full_name}</div>
                <div className="text-[10px] text-slate-400 font-mono">{user.email}</div>
                <div className="text-[9px] text-emerald-400 font-mono mt-0.5 uppercase">Role: {user.role || 'CUSTOMER'}</div>
              </div>
              <button
                onClick={logout}
                className="px-2.5 py-1 rounded-lg text-xs font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 flex items-center space-x-1"
              >
                <LogOut className="h-3 w-3" />
                <span>Logout</span>
              </button>
            </div>
          )}

          {isAdmin && (
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-mono text-slate-500 block px-1">Switch View</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => {
                    if (onViewChange) onViewChange('banking');
                    setMobileMenuOpen(false);
                  }}
                  className={`p-2.5 rounded-lg border text-left text-xs font-medium transition-colors flex items-center space-x-2 ${
                    currentView === 'banking'
                      ? 'bg-white text-slate-950 font-semibold'
                      : 'bg-black/30 border-white/[0.08] text-slate-300'
                  }`}
                >
                  <CreditCard className="h-3.5 w-3.5" />
                  <span>Banking</span>
                </button>
                <button
                  onClick={() => {
                    if (onViewChange) onViewChange('admin');
                    setMobileMenuOpen(false);
                  }}
                  className={`p-2.5 rounded-lg border text-left text-xs font-medium transition-colors flex items-center space-x-2 ${
                    currentView === 'admin'
                      ? 'bg-emerald-500 text-slate-950 font-semibold'
                      : 'bg-black/30 border-white/[0.08] text-slate-300'
                  }`}
                >
                  <Database className="h-3.5 w-3.5" />
                  <span>RAG Console</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
