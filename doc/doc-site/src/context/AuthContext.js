import React, { createContext, useContext, useState, useEffect } from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { normalizeRole, getRoleDisplayName } from '../config/roles';
import { setAuthToken } from '../api/auth';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const { siteConfig } = useDocusaurusContext();
  const authEnabled = siteConfig.customFields?.authEnabled !== false;
  const defaultRole = normalizeRole(siteConfig.customFields?.defaultRole || 'student');
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authEnabled) {
      setUser({
        email: `local-${defaultRole}@aura.local`,
        username: `local-${defaultRole}@aura.local`,
        name: 'Local Documentation User',
      });
      setRole(defaultRole);
      setAuthToken(null);
      setLoading(false);
      return;
    }

    // Only access localStorage in browser (SSR safety)
    if (typeof window === 'undefined') {
      setLoading(false);
      return;
    }

    try {
      const storedUser = localStorage.getItem('aura_doc_user');
      const storedRole = localStorage.getItem('aura_doc_role');
      const storedToken = localStorage.getItem('aura_doc_token');

      if (storedUser && storedRole) {
        setUser(JSON.parse(storedUser));
        setRole(normalizeRole(storedRole));
        if (storedToken) {
          setAuthToken(storedToken);
        }
      }
    } catch (error) {
      console.error('Error loading auth state:', error);
    }

    setLoading(false);
  }, [authEnabled, defaultRole]);

  const login = (userData, userRole, token = null) => {
    if (typeof window === 'undefined') return;

    const normalizedRole = normalizeRole(userRole);

    try {
      localStorage.setItem('aura_doc_user', JSON.stringify(userData));
      localStorage.setItem('aura_doc_role', normalizedRole);
      if (token) {
        localStorage.setItem('aura_doc_token', token);
        setAuthToken(token);
      }

      setUser(userData);
      setRole(normalizedRole);
    } catch (error) {
      console.error('Error saving auth state:', error);
    }
  };

  const logout = () => {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem('aura_doc_user');
      localStorage.removeItem('aura_doc_role');
      localStorage.removeItem('aura_doc_token');
      setAuthToken(null);
    } catch (error) {
      console.error('Error clearing auth state:', error);
    }

    setUser(null);
    setRole(null);
  };

  const value = {
    user,
    role,
    roleDisplayName: role ? getRoleDisplayName(role) : null,
    loading,
    isAuthenticated: !!user && !!role,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
