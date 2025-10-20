import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    // Auto-login for localhost development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console.log('🔓 Local development mode: Auto-login enabled');
      setIsAuthenticated(true);
      setUsername('dev-user');
      setToken('dev-token');
      localStorage.setItem('auth_token', 'dev-token');
      localStorage.setItem('auth_username', 'dev-user');
      setLoading(false);
      return;
    }

    const storedToken = localStorage.getItem('auth_token');
    const storedUsername = localStorage.getItem('auth_username');

    if (storedToken && storedUsername) {
      // Verify the token is still valid
      verifyToken(storedToken, storedUsername);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (token: string, username: string) => {
    try {
      const response = await fetch(`/api/auth/verify?token=${token}`);

      if (response.ok) {
        const data = await response.json();
        if (data.valid) {
          setIsAuthenticated(true);
          setUsername(username);
          setToken(token);
        } else {
          // Token invalid, clear storage
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_username');
        }
      } else {
        // Token invalid, clear storage
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
      }
    } catch (err) {
      console.error('Error verifying token:', err);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_username');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store token and username
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('auth_username', data.username);

        setIsAuthenticated(true);
        setUsername(data.username);
        setToken(data.token);
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
        await fetch('/api/auth/logout', {
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

    // Clear local state and storage
    setIsAuthenticated(false);
    setUsername(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_username');
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        token,
        login,
        logout,
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
