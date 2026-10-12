import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient.js';
import { getBackendUrl, getFrontendUrl } from '../config/api.js';
import { getInitialRecoveryParams } from '../utils/routes.js';

const AuthContext = createContext({
  user: null,
  session: null,
  loading: true,
  isConfigured: false,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  signInWithOAuth: async () => {},
  signInWithGoogle: async () => {},
  resetPasswordForEmail: async () => {},
  updatePassword: async () => {},
  isPasswordRecovery: false,
  authModalOpen: false,
  authModalMode: 'signin',
  openAuthModal: () => {},
  closeAuthModal: () => {},
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('signin');
  const [isPasswordRecovery, setIsPasswordRecovery] = useState(false);
  const isConfigured = isSupabaseConfigured();

  const syncBackendUser = async (currentSession) => {
    if (!currentSession?.access_token) return;
    try {
      await axios.post(
        `${getBackendUrl()}/api/auth/sync`,
        { email: currentSession.user?.email },
        {
          headers: {
            Authorization: `Bearer ${currentSession.access_token}`,
          },
        }
      );
    } catch (err) {
      // Non-blocking sync notice
      console.warn('Backend user profile sync notice:', err?.response?.data?.error || err.message);
    }
  };

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    const initialParams = getInitialRecoveryParams();
    if (initialParams.isRecovery && !initialParams.hasError) {
      setIsPasswordRecovery(true);
    }

    // 1. Get initial session
    supabase.auth.getSession().then(({ data: { session: initialSession }, error }) => {
      if (!error && initialSession) {
        setSession(initialSession);
        setUser(initialSession.user ?? null);
        syncBackendUser(initialSession);
        if (initialParams.isRecovery && !initialParams.hasError) {
          setIsPasswordRecovery(true);
        }
      }
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });

    // 2. Listen to state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);
      if (event === 'PASSWORD_RECOVERY') {
        setIsPasswordRecovery(true);
      } else if (event === 'SIGNED_IN' && initialParams.isRecovery && !initialParams.hasError) {
        setIsPasswordRecovery(true);
      }
      if (newSession && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED')) {
        syncBackendUser(newSession);
      }
      setLoading(false);
    });

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  const signIn = async (email, password) => {
    if (!supabase) {
      throw new Error('Supabase client is not configured. Please check environment variables.');
    }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    setSession(data.session);
    setUser(data.user);
    if (data.session) {
      syncBackendUser(data.session);
    }
    return data;
  };

  const signUp = async (email, password) => {
    if (!supabase) {
      throw new Error('Supabase client is not configured. Please check environment variables.');
    }
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
    if (data.session) {
      setSession(data.session);
      setUser(data.user);
      syncBackendUser(data.session);
    }
    return data;
  };

  const signOut = async () => {
    if (!supabase) return;
    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.error('Sign out error:', err);
    } finally {
      setUser(null);
      setSession(null);
      setIsPasswordRecovery(false);
    }
  };

  const signInWithOAuth = async (provider = 'google', customOptions = {}) => {
    if (!supabase) {
      throw new Error('Supabase client is not configured. Please check environment variables.');
    }

    const currentEmail = user?.email || session?.user?.email || null;
    const redirectTo = customOptions.redirectTo || getFrontendUrl();

    const queryParams = { ...(customOptions.queryParams || {}) };
    if (currentEmail && !queryParams.login_hint) {
      queryParams.login_hint = currentEmail;
    }

    const options = {
      ...customOptions,
      redirectTo,
    };

    if (Object.keys(queryParams).length > 0) {
      options.queryParams = queryParams;
    }

    const { data, error } = await supabase.auth.signInWithOAuth({
      provider,
      options,
    });

    if (error) throw error;
    return data;
  };

  const signInWithGoogle = async (customOptions = {}) => {
    return signInWithOAuth('google', customOptions);
  };

  const resetPasswordForEmail = async (email) => {
    if (!supabase) {
      throw new Error('Supabase client is not configured. Please check environment variables.');
    }
    const redirectTo = `${getFrontendUrl()}/reset-password`;
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo,
    });
    if (error) throw error;
    return data;
  };

  const updatePassword = async (newPassword) => {
    if (!supabase) {
      throw new Error('Supabase client is not configured. Please check environment variables.');
    }
    const { data, error } = await supabase.auth.updateUser({
      password: newPassword,
    });
    if (error) throw error;
    return data;
  };

  const openAuthModal = (mode = 'signin') => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setAuthModalOpen(false);
    setAuthModalMode('signin');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        isConfigured,
        signIn,
        signUp,
        signOut,
        signInWithOAuth,
        signInWithGoogle,
        resetPasswordForEmail,
        updatePassword,
        isPasswordRecovery,
        authModalOpen,
        authModalMode,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
