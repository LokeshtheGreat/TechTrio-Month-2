import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient.js';
import { getBackendUrl } from '../config/api.js';

const AuthContext = createContext({
  user: null,
  session: null,
  loading: true,
  isConfigured: false,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  authModalOpen: false,
  openAuthModal: () => {},
  closeAuthModal: () => {},
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authModalOpen, setAuthModalOpen] = useState(false);
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

    // 1. Get initial session
    supabase.auth.getSession().then(({ data: { session: initialSession }, error }) => {
      if (!error && initialSession) {
        setSession(initialSession);
        setUser(initialSession.user ?? null);
        syncBackendUser(initialSession);
      }
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });

    // 2. Listen to state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);
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
    }
  };

  const openAuthModal = () => setAuthModalOpen(true);
  const closeAuthModal = () => setAuthModalOpen(false);

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
        authModalOpen,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
