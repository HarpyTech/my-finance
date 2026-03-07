import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiRequest } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState({ authenticated: false, user: null, role: null });
  const [loading, setLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      const data = await apiRequest('/auth/session');
      setSession(data);
    } catch (error) {
      setSession({ authenticated: false, user: null, role: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  const login = async (username, password) => {
    await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    await refreshSession();
  };

  const register = async (username, password) => {
    await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  };

  const logout = async () => {
    await apiRequest('/auth/logout', { method: 'POST' });
    setSession({ authenticated: false, user: null, role: null });
  };

  const value = useMemo(
    () => ({ session, loading, login, register, logout, refreshSession }),
    [session, loading, refreshSession]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
