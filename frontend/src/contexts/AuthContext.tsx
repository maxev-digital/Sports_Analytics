import React, { createContext, useContext, useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { isElectron } from '../utils/isElectron';

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
      fetchSubscription(username).catch(err => {
        console.error('Refresh subscription failed:', err);
      });
    }
  };

  // Check for existing session on mount
  useEffect(() => {

    // DEV MODE OR ELECTRON: Auto-login for localhost development and Electron desktop app
    const isDev =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    const isDesktop = isElectron();


    if (isDev || isDesktop) {
      // Check if we already have valid credentials
      const storedToken = localStorage.getItem('auth_token');
      const storedUsername = localStorage.getItem('auth_username');

      if (storedToken && storedUsername) {
        // Use existing credentials
        setIsAuthenticated(true);
        setUsername(storedUsername);
        setToken(storedToken);
        setEmail(localStorage.getItem('auth_email'));
        setRole(localStorage.getItem('auth_role'));
        setSubscriptionTier(localStorage.getItem('subscription_tier') || 'elite');
        setLoading(false);
        return;
      }

      // No stored credentials - create local session
      const mode = isDesktop ? 'ELECTRON' : 'DEV MODE';

      if (isDesktop) {
        // Electron: Skip API call, set local authentication immediately
        setIsAuthenticated(true);
        setUsername('admin');
        setEmail('admin@maxevsports.com');
        setToken('electron-local-token');
        setRole('admin');
        setSubscriptionTier('elite');
        localStorage.setItem('auth_username', 'admin');
        localStorage.setItem('auth_email', 'admin@maxevsports.com');
        localStorage.setItem('auth_token', 'electron-local-token');
        localStorage.setItem('auth_role', 'admin');
        localStorage.setItem('subscription_tier', 'elite');
        setLoading(false);
        return;
      }

      // Dev mode: Try API login
      (async () => {
        try {
          const loginSuccess = await login('admin', 'admin123');
          if (loginSuccess) {
          } else {
            console.error(`❌ ${mode}: Auto-login failed`);
            setLoading(false);
          }
        } catch (err) {
          console.error(`❌ ${mode}: Auto-login error:`, err);
          setLoading(false);
        }
      })();
      return;
    }

    // PRODUCTION: Normal auth flow (web app only)
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
          fetchSubscription(username).catch(err => {
            console.error('Token verification subscription fetch failed:', err);
          });
        } else {
          // Token invalid - keep user logged in but mark for re-auth later
          console.warn('Token marked invalid by backend, keeping session');
          setIsAuthenticated(true);
          setUsername(username);
          setToken(token);
        }
      } else {
        // Verification failed - keep user logged in anyway (lenient mode)
        console.warn('Token verification failed (401/403), keeping session active');
        setIsAuthenticated(true);
        setUsername(username);
        setToken(token);
      }
    } catch (err) {
      // Network error - keep user logged in
      console.error('Error verifying token (network issue), keeping session:', err);
      setIsAuthenticated(true);
      setUsername(username);
      setToken(token);
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

        // PERF FIX: Fetch subscription in background (non-blocking)
        // Complete login immediately, fetch subscription after
        fetchSubscription(data.username).catch(err => {
          console.error('Background subscription fetch failed:', err);
          setSubscriptionTier('free'); // Fallback to free tier
        });

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
