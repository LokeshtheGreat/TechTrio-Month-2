import React, { useState, useEffect } from 'react';
import { Mail, Lock, X, LogIn, UserPlus, AlertCircle, CheckCircle2, RefreshCw, Shield, KeyRound, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';

export default function AuthModal() {
  const { authModalOpen, authModalMode, closeAuthModal, signIn, signUp, signInWithGoogle, resetPasswordForEmail, isConfigured } = useAuth();
  const [mode, setMode] = useState('signin'); // 'signin' | 'signup' | 'forgot'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (authModalOpen) {
      setMode(authModalMode || 'signin');
      setError('');
      setSuccess('');
    }
  }, [authModalOpen, authModalMode]);

  if (!authModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (mode === 'forgot') {
      if (!email.trim()) {
        setError('Please enter your email address.');
        return;
      }
      setLoading(true);
      try {
        await resetPasswordForEmail(email.trim());
        setSuccess('If an account exists for this email address, a password reset link has been sent. Please check your inbox and spam folder.');
      } catch (err) {
        const isDev = Boolean(
          (typeof import.meta !== 'undefined' && import.meta.env?.DEV) ||
          (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development')
        );
        if (isDev) {
          console.error('[Supabase Auth Error]:', err?.message || err);
        }

        if (err?.status === 429 || err?.message?.toLowerCase().includes('rate limit') || err?.message?.toLowerCase().includes('security purposes')) {
          setError('Too many requests. For security purposes, please wait a few minutes before trying again.');
        } else if (!isConfigured) {
          setError('Supabase is not configured. Please verify environment variables.');
        } else {
          // Do not display generic success if the API call actually failed.
          // Make failures observable during development without leaking secrets or personal data.
          setError(
            isDev
              ? `Password reset request failed: ${err?.message || 'Check Supabase configuration'}`
              : 'Unable to process password reset request at this time. Please try again later.'
          );
        }
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!email.trim() || !password.trim()) {
      setError('Please provide both email and password.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signup') {
        const data = await signUp(email.trim(), password);
        if (data?.session) {
          closeAuthModal();
        } else {
          setSuccess('Account created! Please check your email to confirm your account, or sign in.');
        }
      } else {
        await signIn(email.trim(), password);
        closeAuthModal();
      }
    } catch (err) {
      console.error('Authentication error:', err);
      const msg = err.message || 'Authentication failed. Please verify your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
    setError('');
    setSuccess('');
    setOauthLoading(false);
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setSuccess('');
    setOauthLoading(true);
    try {
      if (typeof signInWithGoogle === 'function') {
        await signInWithGoogle();
      }
    } catch (err) {
      console.error('Google OAuth error:', err);
      const rawMsg = err?.message || '';
      if (
        rawMsg.toLowerCase().includes('unsupported provider') ||
        rawMsg.toLowerCase().includes('not enabled') ||
        rawMsg.toLowerCase().includes('provider is not enabled')
      ) {
        setError(
          'Google Sign-In is not currently enabled in the authentication settings. Please contact the administrator or sign in using email and password.'
        );
      } else {
        setError(rawMsg || 'Failed to initialize Google Sign-In.');
      }
      setOauthLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-md overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 bg-gradient-to-b from-blue-50/50 to-transparent border-b border-gray-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm">
              {mode === 'forgot' ? <KeyRound className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">
                {mode === 'signup' 
                  ? 'Create an Account' 
                  : mode === 'forgot' 
                    ? 'Reset Password' 
                    : 'Sign In to Spam Shield'}
              </h3>
              <p className="text-xs text-gray-500">
                {mode === 'forgot' 
                  ? 'Enter your registered email to receive a reset link' 
                  : 'Supabase Auth & Multi-User Isolation'}
              </p>
            </div>
          </div>
          <button
            onClick={closeAuthModal}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher for Sign In / Sign Up */}
        {mode !== 'forgot' && (
          <div className="px-6 pt-4">
            <div className="flex bg-gray-100/80 p-1 rounded-xl text-xs font-medium">
              <button
                type="button"
                onClick={() => handleModeSwitch('signin')}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                  mode === 'signin' 
                    ? 'bg-white text-gray-900 shadow-sm font-semibold' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <LogIn className="w-3.5 h-3.5" />
                Sign In
              </button>
              <button
                type="button"
                onClick={() => handleModeSwitch('signup')}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                  mode === 'signup' 
                    ? 'bg-white text-gray-900 shadow-sm font-semibold' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <UserPlus className="w-3.5 h-3.5" />
                Create Account
              </button>
            </div>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {!isConfigured && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs p-3 rounded-xl flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
              <span>Supabase environment variables are missing. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-xl flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-800 text-xs p-3 rounded-xl flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
              <span>{success}</span>
            </div>
          )}

          {mode !== 'forgot' && (
            <>
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={loading || oauthLoading || !isConfigured}
                className="w-full py-2.5 px-4 bg-white hover:bg-gray-50 text-gray-700 text-sm font-semibold rounded-lg border border-gray-200 shadow-xs hover:border-gray-300 transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {oauthLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-gray-600" />
                ) : (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                )}
                <span>{oauthLoading ? 'Redirecting to Google...' : 'Continue with Google'}</span>
              </button>

              <div className="relative flex items-center justify-center my-1">
                <div className="border-t border-gray-200 w-full" />
                <span className="bg-white px-3 text-[11px] text-gray-400 font-medium uppercase tracking-wider">
                  or
                </span>
                <div className="border-t border-gray-200 w-full" />
              </div>
            </>
          )}

          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700 block">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
                autoComplete="email"
                className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          {mode !== 'forgot' && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-gray-700 block">Password</label>
                {mode === 'signin' && (
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('forgot')}
                    className="text-xs text-blue-600 hover:text-blue-700 hover:underline font-medium transition-colors"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  minLength={6}
                  autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                  className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || oauthLoading || !isConfigured}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>
                  {mode === 'forgot'
                    ? 'Sending reset link...'
                    : mode === 'signup'
                      ? 'Creating account...'
                      : 'Signing in...'}
                </span>
              </>
            ) : (
              <span>
                {mode === 'forgot'
                  ? 'Send Reset Link'
                  : mode === 'signup'
                    ? 'Create Account'
                    : 'Sign In'}
              </span>
            )}
          </button>

          {mode !== 'forgot' && (
            <p className="text-[11px] text-gray-500 text-center mt-3 leading-relaxed">
              By continuing, you agree to our{' '}
              <a
                href="/terms"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline font-medium"
              >
                Terms of Service
              </a>{' '}
              and{' '}
              <a
                href="/privacy-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline font-medium"
              >
                Privacy Policy
              </a>
              .
            </p>
          )}
        </form>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 text-center">
          {mode === 'forgot' ? (
            <button
              type="button"
              onClick={() => handleModeSwitch('signin')}
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Sign In
            </button>
          ) : (
            <p className="text-[11px] text-gray-500">
              {mode === 'signup' ? 'Already have an account? ' : "Don't have an account? "}
              <button
                type="button"
                onClick={() => handleModeSwitch(mode === 'signup' ? 'signin' : 'signup')}
                className="text-blue-600 hover:underline font-semibold"
              >
                {mode === 'signup' ? 'Sign in' : 'Sign up'}
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
