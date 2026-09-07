'use client';

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '@/context/AuthContext';
import { User, Lock, X, Loader2, LogIn, UserPlus } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  theme?: 'dark' | 'light';
}

export default function AuthModal({ isOpen, onClose, theme = 'light' }: Props) {
  const { login, register } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }

    if (isSignUp && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      setSubmitting(true);
      if (isSignUp) {
        await register(username.trim(), password);
      } else {
        await login(username.trim(), password);
      }
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return createPortal(
    <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
      <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-txtPrimary relative">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400 shrink-0">
              {isSignUp ? <UserPlus className="w-5 h-5" /> : <LogIn className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="font-bold text-base text-txtPrimary">
                {isSignUp ? 'Create an Account' : 'Sign In to Script Supervisor'}
              </h3>
              <p className="text-xs text-txtSecondary mt-0.5">
                {isSignUp
                  ? 'Sign up to start saving and managing your isolated screenplay projects.'
                  : 'Enter your credentials to access your screenplay workspace.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-panel border border-border rounded-xl p-1 gap-1">
          <button
            type="button"
            onClick={() => { setIsSignUp(false); setError(null); }}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition ${
              !isSignUp ? 'bg-card text-txtPrimary shadow-sm' : 'text-txtSecondary hover:text-txtPrimary'
            }`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => { setIsSignUp(true); setError(null); }}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition ${
              isSignUp ? 'bg-card text-txtPrimary shadow-sm' : 'text-txtSecondary hover:text-txtPrimary'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-600 dark:text-red-400 text-xs font-medium">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-txtPrimary mb-1.5">Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-txtSecondary absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3.5 py-2.5 bg-panel border border-border rounded-xl text-xs text-txtPrimary placeholder:text-txtMuted focus:outline-none focus:border-secondary focus:ring-2 focus:ring-blue-500/20 font-medium"
                autoFocus
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-txtPrimary mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-txtSecondary absolute left-3 top-3" />
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3.5 py-2.5 bg-panel border border-border rounded-xl text-xs text-txtPrimary placeholder:text-txtMuted focus:outline-none focus:border-secondary focus:ring-2 focus:ring-blue-500/20 font-medium"
                required
              />
            </div>
          </div>

          {isSignUp && (
            <div>
              <label className="block text-xs font-bold text-txtPrimary mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-txtSecondary absolute left-3 top-3" />
                <input
                  type="password"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 bg-panel border border-border rounded-xl text-xs text-txtPrimary placeholder:text-txtMuted focus:outline-none focus:border-secondary focus:ring-2 focus:ring-blue-500/20 font-medium"
                  required
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !username.trim() || !password.trim()}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg disabled:opacity-50 shrink-0"
            >
              {submitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : isSignUp ? (
                <UserPlus className="w-3.5 h-3.5" />
              ) : (
                <LogIn className="w-3.5 h-3.5" />
              )}
              {isSignUp ? 'Create Account' : 'Log In'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
