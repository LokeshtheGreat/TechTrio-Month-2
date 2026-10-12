import React, { useState, useEffect } from 'react';
import { Shield, KeyRound, Lock, CheckCircle2, AlertCircle, RefreshCw, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient.js';
import { getInitialRecoveryParams } from '../utils/routes.js';

export default function ResetPassword({ onNavigate }) {
  const { isPasswordRecovery, updatePassword, openAuthModal, signOut } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifyingSession, setVerifyingSession] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let authListener = null;
    let timeoutId = null;

    const initialParams = getInitialRecoveryParams();

    // 1. If the URL arrived with an error parameter from Supabase (e.g. otp_expired, access_denied)
    if (initialParams.hasError) {
      setIsAuthorized(false);
      setVerifyingSession(false);
      setError(
        initialParams.errorDescription ||
        'This password reset link is invalid, has expired, or has already been used.'
      );
      return;
    }

    const validateRecoverySession = async () => {
      // 2. If AuthContext already confirmed recovery session
      if (isPasswordRecovery) {
        if (isMounted) {
          setIsAuthorized(true);
          setVerifyingSession(false);
        }
        return;
      }

      if (!supabase || !isSupabaseConfigured()) {
        if (isMounted) {
          setIsAuthorized(false);
          setVerifyingSession(false);
        }
        return;
      }

      // 3. Handle OTP / token_hash flow if present in URL
      if (initialParams.tokenHash && (initialParams.type === 'recovery' || !initialParams.type)) {
        try {
          const { data, error: otpError } = await supabase.auth.verifyOtp({
            token_hash: initialParams.tokenHash,
            type: 'recovery',
          });
          if (isMounted) {
            if (!otpError && data?.session) {
              setIsAuthorized(true);
              setVerifyingSession(false);
              return;
            } else if (otpError) {
              console.error('OTP recovery error:', otpError.message);
              setIsAuthorized(false);
              setVerifyingSession(false);
              setError(otpError.message || 'This password reset link is invalid or has expired.');
              return;
            }
          }
        } catch (otpErr) {
          if (isMounted) {
            setIsAuthorized(false);
            setVerifyingSession(false);
            setError(otpErr?.message || 'This password reset link is invalid or has expired.');
            return;
          }
        }
      }

      // 4. Handle PKCE code flow if present in URL and not yet consumed
      if (initialParams.code) {
        try {
          const { data, error: codeError } = await supabase.auth.exchangeCodeForSession(initialParams.code);
          if (isMounted && !codeError && data?.session) {
            setIsAuthorized(true);
            setVerifyingSession(false);
            return;
          }
        } catch {
          // May have already been exchanged automatically by GoTrue client
        }
      }

      // 5. Inspect existing Supabase session
      try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        if (isMounted && !sessionError && session) {
          if (initialParams.isRecovery || isPasswordRecovery) {
            setIsAuthorized(true);
            setVerifyingSession(false);
            return;
          }
        }
      } catch (err) {
        console.error('Error checking recovery session:', err?.message || err);
      }

      // 6. If session not yet resolved, listen to onAuthStateChange and wait for callback
      if (supabase && isMounted) {
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
          if (!isMounted) return;
          if (event === 'PASSWORD_RECOVERY') {
            setIsAuthorized(true);
            setVerifyingSession(false);
            if (timeoutId) clearTimeout(timeoutId);
          } else if (event === 'SIGNED_IN' && session && initialParams.isRecovery) {
            setIsAuthorized(true);
            setVerifyingSession(false);
            if (timeoutId) clearTimeout(timeoutId);
          }
        });
        authListener = subscription;

        // Safety fallback timer: only mark unauthorized after giving callback time to complete
        timeoutId = setTimeout(() => {
          if (!isMounted) return;
          supabase.auth.getSession().then(({ data: { session } }) => {
            if (isMounted) {
              if (session && (initialParams.isRecovery || isPasswordRecovery)) {
                setIsAuthorized(true);
              } else {
                setIsAuthorized(false);
              }
              setVerifyingSession(false);
            }
          }).catch(() => {
            if (isMounted) {
              setIsAuthorized(false);
              setVerifyingSession(false);
            }
          });
        }, 2500);
      } else if (isMounted) {
        setIsAuthorized(false);
        setVerifyingSession(false);
      }
    };

    validateRecoverySession();

    return () => {
      isMounted = false;
      if (authListener) authListener.unsubscribe();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isPasswordRecovery]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!newPassword || !confirmPassword) {
      setError('Please fill in both password fields.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify and try again.');
      return;
    }

    setLoading(true);
    try {
      if (updatePassword) {
        await updatePassword(newPassword);
      } else if (supabase) {
        const { error: updateError } = await supabase.auth.updateUser({ password: newPassword });
        if (updateError) throw updateError;
      } else {
        throw new Error('Supabase client is not available.');
      }

      setSuccess(true);
      // Clean up the recovery session so user signs in cleanly with their new password
      try {
        if (signOut) {
          await signOut();
        } else if (supabase) {
          await supabase.auth.signOut();
        }
      } catch (signOutErr) {
        console.warn('Sign out cleanup notice:', signOutErr);
      }
    } catch (err) {
      console.error('Password reset failure:', err);
      setError(err?.message || 'Failed to update password. Your reset link may have expired.');
    } finally {
      setLoading(false);
    }
  };

  const handleReturnToLogin = () => {
    if (onNavigate) {
      onNavigate('app');
    }
    if (openAuthModal) {
      openAuthModal('signin');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-between text-gray-800">
      {/* Navigation Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate && onNavigate('app')}
              className="flex items-center gap-2 text-blue-600 font-bold text-lg hover:opacity-90 transition-opacity"
              title="Return to Email Spam Shield"
            >
              <Shield className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <span>Spam Shield</span>
            </button>
            <span className="text-gray-300">/</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              Account Security
            </span>
          </div>

          <button
            onClick={() => onNavigate && onNavigate('app')}
            className="flex items-center gap-1.5 text-xs font-medium text-gray-600 hover:text-blue-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 my-8">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {verifyingSession ? (
            <div className="p-10 text-center space-y-4">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              <h3 className="text-base font-semibold text-gray-900">Verifying Reset Link</h3>
              <p className="text-xs text-gray-500">Checking your password recovery authorization...</p>
            </div>
          ) : !isAuthorized ? (
            /* Unauthorized / Expired Link State (Requirement 6) */
            <div className="p-8 space-y-5 text-center">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto border border-amber-200">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-gray-900">Invalid or Expired Reset Link</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  This password reset link is invalid, has expired, or has already been used.
                  For your security, reset links can only be used once.
                </p>
              </div>

              <div className="pt-2 space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    if (onNavigate) onNavigate('app');
                    if (openAuthModal) openAuthModal('forgot');
                  }}
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
                >
                  Request a New Reset Link
                </button>
                <button
                  type="button"
                  onClick={() => onNavigate && onNavigate('app')}
                  className="w-full py-2.5 px-4 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs font-medium rounded-lg border border-gray-200 transition-all"
                >
                  Return to Dashboard
                </button>
              </div>
            </div>
          ) : success ? (
            /* Success State */
            <div className="p-8 space-y-5 text-center">
              <div className="w-12 h-12 rounded-2xl bg-green-50 text-green-600 flex items-center justify-center mx-auto border border-green-200">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-gray-900">Password Reset Complete</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Your password has been successfully updated. You can now sign in with your new credentials.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleReturnToLogin}
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center justify-center gap-2"
                >
                  <span>Sign In Now</span>
                </button>
              </div>
            </div>
          ) : (
            /* Reset Password Form */
            <div>
              {/* Card Header */}
              <div className="p-6 bg-gradient-to-b from-blue-50/50 to-transparent border-b border-gray-100 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm flex-shrink-0">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Set New Password</h3>
                  <p className="text-xs text-gray-500">Create a secure password for your account</p>
                </div>
              </div>

              {/* Form Body */}
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-xl flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700 block">New Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 6 characters"
                      required
                      minLength={6}
                      autoComplete="new-password"
                      className="w-full pl-9 pr-10 py-2 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700 block">Confirm New Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter your new password"
                      required
                      minLength={6}
                      autoComplete="new-password"
                      className="w-full pl-9 pr-10 py-2 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                      aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Updating Password...</span>
                    </>
                  ) : (
                    <span>Update Password</span>
                  )}
                </button>
              </form>

              {/* Card Footer */}
              <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 text-center">
                <button
                  type="button"
                  onClick={handleReturnToLogin}
                  className="text-xs text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Return to Sign In
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Global Footer */}
      <footer className="border-t border-gray-200 bg-white py-6">
        <div className="max-w-5xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 gap-3">
          <p>© 2026 Email Spam Shield. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <a
              href="/privacy-policy"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate && onNavigate('privacy-policy');
                }
              }}
              className="hover:text-blue-600 transition-colors"
            >
              Privacy Policy
            </a>
            <span>•</span>
            <a
              href="/terms"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate && onNavigate('terms');
                }
              }}
              className="hover:text-blue-600 transition-colors"
            >
              Terms of Service
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
