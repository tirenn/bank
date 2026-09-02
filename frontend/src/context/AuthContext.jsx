import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, bankingApi } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [account, setAccount] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('bank_token'));
  const [loading, setLoading] = useState(true);

  const fetchUserData = async () => {
    try {
      const me = await authApi.getMe();
      setUser(me);
      try {
        const accListRes = await bankingApi.getAccounts();
        const accList = accListRes.accounts || [];
        setAccounts(accList);
        if (accList.length > 0) {
          setAccount(accList[0]);
        } else {
          setAccount(null);
        }
      } catch (accErr) {
        console.warn('User has no accounts:', accErr);
        setAccounts([]);
        setAccount(null);
      }
    } catch (err) {
      console.error('Error fetching user data:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUserData();
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem('bank_token', data.token);
    setToken(data.token);
    setUser(data.user);
    try {
      const accListRes = await bankingApi.getAccounts();
      const accList = accListRes.accounts || [];
      setAccounts(accList);
      if (accList.length > 0) {
        setAccount(accList[0]);
      }
    } catch (accErr) {
      console.warn('User has no bank account:', accErr);
      setAccounts([]);
      setAccount(null);
    }
    return data;
  };

  const register = async (email, password, fullName) => {
    const data = await authApi.register(email, password, fullName);
    localStorage.setItem('bank_token', data.token);
    setToken(data.token);
    setUser(data.user);
    try {
      const accListRes = await bankingApi.getAccounts();
      const accList = accListRes.accounts || [];
      setAccounts(accList);
      if (accList.length > 0) {
        setAccount(accList[0]);
      }
    } catch (accErr) {
      console.warn('User has no bank account:', accErr);
      setAccounts([]);
      setAccount(null);
    }
    return data;
  };

  const logout = () => {
    localStorage.removeItem('bank_token');
    setToken(null);
    setUser(null);
    setAccount(null);
    setAccounts([]);
  };

  const selectAccount = (selectedAcc) => {
    setAccount(selectedAcc);
  };

  const refreshAccount = async () => {
    try {
      const accListRes = await bankingApi.getAccounts();
      const accList = accListRes.accounts || [];
      setAccounts(accList);
      if (accList.length > 0) {
        // preserve currently selected account if possible
        setAccount((prev) => {
          if (!prev) return accList[0];
          const match = accList.find((a) => a.id === prev.id);
          return match || accList[0];
        });
      } else {
        setAccount(null);
      }
    } catch (e) {
      console.error('Failed to refresh accounts', e);
    }
  };

  const isAdmin = (user?.role || '').toUpperCase() === 'ADMIN';

  return (
    <AuthContext.Provider
      value={{
        user,
        account,
        accounts,
        token,
        isAdmin,
        loading,
        login,
        register,
        logout,
        selectAccount,
        refreshAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};


export const useAuth = () => useContext(AuthContext);
