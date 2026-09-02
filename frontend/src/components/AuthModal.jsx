import React, { useState } from 'react';
import { Landmark, Shield, AlertCircle, ArrowRight, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const AuthModal = () => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('john.doe@bank.com');
  const [password, setPassword] = useState('password123');
  const [fullName, setFullName] = useState('John Doe');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Authentication failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoUser = (userEmail, userPass, name) => {
    setIsRegister(false);
    setEmail(userEmail);
    setPassword(userPass);
    setFullName(name);
  };

  return (
    <div className="min-h-screen bg-[#08090d] flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-sm bg-[#0f1117] border border-white/[0.08] rounded-2xl p-7 shadow-xl">

        {/* Brand header */}
        <div className="text-center space-y-2 mb-6">
          <div className="inline-flex items-center justify-center h-11 w-11 rounded-xl bg-white/[0.06] border border-white/[0.1] text-emerald-400 mb-1">
            <Landmark className="h-5 w-5" />
          </div>
          <h1 className="text-lg font-semibold tracking-tight text-white">
            Tirenn Core Banking
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Secured Terminal Access
          </p>
        </div>

        {/* Demo Personas */}
        <div className="mb-5 p-3 rounded-xl bg-black/40 border border-white/[0.06] text-xs">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block mb-2">
            Instant Demo Logins
          </span>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setDemoUser('admin@bank.com', 'password123', 'System Administrator')}
              className={`w-full p-2 rounded-lg border text-left transition-colors cursor-pointer flex items-center justify-between ${email === 'admin@bank.com' ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-slate-200'
                }`}
            >
              <div>
                <div className="font-medium text-xs text-slate-200">System Administrator</div>
                <div className="text-[10px] text-slate-500 font-mono">admin@bank.com</div>
              </div>
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-semibold">
                ROLE: ADMIN
              </span>
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDemoUser('john.doe@bank.com', 'password123', 'John Doe')}
                className={`p-2 rounded-lg border text-left transition-colors cursor-pointer ${email === 'john.doe@bank.com' ? 'bg-white/[0.08] border-emerald-500/40 text-slate-100' : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-slate-200'
                  }`}
              >
                <div className="font-medium text-xs text-slate-200">John Doe</div>
                <div className="text-[10px] text-slate-500 font-mono">$12,540.50 (User)</div>
              </button>
              <button
                type="button"
                onClick={() => setDemoUser('sarah.smith@bank.com', 'password123', 'Sarah Smith')}
                className={`p-2 rounded-lg border text-left transition-colors cursor-pointer ${email === 'sarah.smith@bank.com' ? 'bg-white/[0.08] border-emerald-500/40 text-slate-100' : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-slate-200'
                  }`}
              >
                <div className="font-medium text-xs text-slate-200">Sarah Smith</div>
                <div className="text-[10px] text-slate-500 font-mono">$4,820.00 (User)</div>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {isRegister && (
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Full Legal Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs"
              />
            </div>
          )}

          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 text-xs font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50 cursor-pointer mt-1"
          >
            <span>{loading ? 'Authenticating...' : isRegister ? 'Create Bank Account' : 'Sign In'}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </form>

        {/* Switch Register/Login */}
        <div className="mt-5 text-center text-xs text-slate-400">
          {isRegister ? (
            <span>
              Already registered?{' '}
              <button
                onClick={() => { setIsRegister(false); setError(''); }}
                className="text-emerald-400 hover:underline font-medium cursor-pointer"
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Need a new account?{' '}
              <button
                onClick={() => { setIsRegister(true); setError(''); }}
                className="text-emerald-400 hover:underline font-medium cursor-pointer"
              >
                Open Account
              </button>
            </span>
          )}
        </div>

        {/* Security badge */}
        <div className="mt-5 pt-3.5 border-t border-white/[0.06] flex items-center justify-center space-x-1.5 text-[10px] text-slate-500 font-mono">
          <Shield className="h-3 w-3 text-emerald-400" />
          <span>256-BIT ENCRYPTION • FDIC INSURED</span>
        </div>
      </div>
    </div>
  );
};
