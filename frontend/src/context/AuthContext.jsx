import { createContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser, loginUser, logoutUser, registerUser } from '../services/authService';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('safeconnect_token');
    if (!token) {
      setLoading(false);
      return;
    }

    getCurrentUser()
      .then((response) => {
        setUser(response.data.user);
        setError('');
      })
      .catch(() => {
        localStorage.removeItem('safeconnect_token');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (payload) => {
    try {
      const response = await loginUser(payload);
      const token = response.data.token;
      const userData = response.data.user;
      localStorage.setItem('safeconnect_token', token);
      setUser(userData);
      setError('');
      return response;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  const register = async (payload) => {
    try {
      const response = await registerUser(payload);
      const token = response.data.token;
      const userData = response.data.user;
      localStorage.setItem('safeconnect_token', token);
      setUser(userData);
      setError('');
      return response;
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    }
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.warn('Logout failed on backend', error);
    } finally {
      localStorage.removeItem('safeconnect_token');
      setUser(null);
      setError('');
    }
  };

  const value = useMemo(
    () => ({ user, loading, error, setError, login, register, logout }),
    [user, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
