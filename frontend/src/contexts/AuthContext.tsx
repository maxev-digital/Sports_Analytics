import React, { createContext, useContext, useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  email: string | null;
  token: string | null;
  role: string | null;
  subscriptionTier: string;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshSubscription: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [subscriptionTier, setSubscriptionTier] = useState<string>('free');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch subscription status
  const fetchSubscription = async (userId: string) => {
    try {
      const response = await fetch(getApiUrl(`subscription/status?user_id=${userId}`));
      if (response.ok) {
        const data = await response.json();
        const tier = data.tier || 'free';
        setSubscriptionTier(tier);
        localStorage.setItem('subscription_tier', tier);
        return tier;
      }
    } catch (err) {
      console.error('Error fetching subscription:', err);
    }
    return 'free';
  };

  const refreshSubscription = async () => {
    if (username) {
      await fetchSubscription(username);
    }
  };

  // Check for existing session on mount
  useEffect(() => {
    console.log('🔍 AuthContext: Checking authentication...');
    console.log('🔍 Current hostname:', window.location.hostname);
    console.log('🔍 Current protocol:', window.location.protocol);

    // DEV MODE: Auto-login ONLY for localhost development (not production Electron build)
    const isDev =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    console.log('🔍 isDev?', isDev);

    if (isDev) {
      // Check if we need to set up dev credentials
      const storedToken = localStorage.getItem('auth_token');
      if (!storedToken) {
        console.log('🔧 DEV MODE: Setting up auto-login...');
        localStorage.setItem('auth_token', 'dev_token_12345');
        localStorage.setItem('auth_username', 'admin');
        localStorage.setItem('subscription_tier', 'elite');
      }

      // Set auth state immediately in dev mode
      setIsAuthenticated(true);
      setUsername(localStorage.getItem('auth_username') || 'admin');
      setToken(localStorage.getItem('auth_token') || 'dev_token_12345');
      setSubscriptionTier(localStorage.getItem('subscription_tier') || 'elite');
      setLoading(false);
      console.log('✅ DEV MODE: Auto-logged in as admin with elite tier');
      console.log('✅ Auth state:', { isAuthenticated: true, username: 'admin', tier: 'elite' });
      return;
    }

    // PRODUCTION: Normal auth flow
    console.log('🔒 PRODUCTION MODE: Using normal auth flow');
    const storedToken = localStorage.getItem('auth_token');
    const storedUsername = localStorage.getItem('auth_username');
    const storedEmail = localStorage.getItem('auth_email');
    const storedRole = localStorage.getItem('auth_role');
    const storedTier = localStorage.getItem('subscription_tier') || 'free';

    if (storedToken && storedUsername) {
      setEmail(storedEmail);
      setRole(storedRole);
      setSubscriptionTier(storedTier);
      verifyToken(storedToken, storedUsername);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (token: string, username: string) => {
    try {
      const response = await fetch(getApiUrl(`auth/verify?token=${token}`));

      if (response.ok) {
        const data = await response.json();
        if (data.valid) {
          setIsAuthenticated(true);
          setUsername(username);
          setToken(token);
          await fetchSubscription(username);
        } else {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_username');
          localStorage.removeItem('auth_email');
          localStorage.removeItem('subscription_tier');
        }
      } else {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
        localStorage.removeItem('subscription_tier');
      }
    } catch (err) {
      console.error('Error verifying token:', err);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_username');
      localStorage.removeItem('subscription_tier');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    setError(null);
    setLoading(true);

    try {
      const response = await fetch(getApiUrl('auth/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('auth_username', data.username);
        localStorage.setItem('auth_email', data.email || '');
        localStorage.setItem('auth_role', data.role || 'user');

        setIsAuthenticated(true);
        setUsername(data.username);
        setEmail(data.email || null);
        setToken(data.token);
        setRole(data.role || 'user');

        await fetchSubscription(data.username);

        setLoading(false);
        return true;
      } else {
        setError(data.detail || 'Login failed');
        setLoading(false);
        return false;
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error. Please try again.');
      setLoading(false);
      return false;
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch(getApiUrl('auth/logout'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }

    setIsAuthenticated(false);
    setUsername(null);
    setEmail(null);
    setToken(null);
    setRole(null);
    setSubscriptionTier('free');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_username');
    localStorage.removeItem('auth_email');
    localStorage.removeItem('auth_role');
    localStorage.removeItem('subscription_tier');

    sessionStorage.setItem('manual_logout', 'true');
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        email,
        token,
        role,
        subscriptionTier,
        login,
        logout,
        refreshSubscription,
        loading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
