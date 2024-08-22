import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';


interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => void;
  logout: () => void;
  isLoading: boolean;
}

interface User {
  id: string;
  email: string;
  name: string;
}


export const Config = {
  API_BASE_URL: 'http://localhost:5000',
  API_AUTH_URL: 'http://localhost:5000/api/auth',
};


const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      verifyToken(token);
    } else {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
      setIsLoading(false);
    }
  }, []);

  const verifyToken = async (token: string) => {
    try {
      const response = await axios.get(`${Config.API_BASE_URL}/api/auth/verify`, {
        headers: { Authorization: `Bearer ${token}`}, timeout: 1000
      });
      setUser(response.data.user);
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${Config.API_BASE_URL}/api/auth/login`, { email, password }, { timeout: 1000 });
      const { user, token } = response.data;
      setUser(user);
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    } catch (error) {
      console.error('Login failed:', error);
      let errorMessage = 'An error occurred during login. Please try again.';
      if (axios.isAxiosError(error) && error.response) {
        errorMessage = error.response.data.message || errorMessage;
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = () => {
    window.location.href = `${Config.API_BASE_URL}/api/auth/google`;
  };

  const logout = async () => {
    try {
      await axios.post(`${Config.API_BASE_URL}/api/auth/logout`, { timeout: 1000 });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, loginWithGoogle, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};