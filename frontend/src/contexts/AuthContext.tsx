import React, { createContext, useContext } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Config } from '@/config/config';

// import api from '@/helpers/request';
import { AuthService } from '@/lib/api/services.gen';

interface AuthContextType {
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: (token: string) => Promise<void>;
}

// interface User {
//   id: string;
//   email: string;
//   name: string;
// }

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();


  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => {
      return AuthService.authLogin({
        body: {
          username: email,
          password: password,
        },
      });
    },
    onSuccess: (response) => {
      const { access_token, token_type } = response.data!;
      localStorage.setItem('token', access_token);
    },
    onError: (error: unknown) => {
      console.error('Login failed:', error);
      let errorMessage = 'An error occurred during login. Please try again.';
      if (axios.isAxiosError(error) && error.response) {
        errorMessage = error.response.data.message || errorMessage;
      }
      throw error;
    },
  });

  const logoutMutation = useMutation({
    mutationFn: (token: string) => {
      // Update this to use the new API client when a logout endpoint is available
      // For now, we'll keep the existing code
      return axios.post(`${Config.API_AUTH_URL}/logout`, {}, { headers: { Authorization: `Bearer ${token}` } });
    },
    onSettled: () => {
      localStorage.removeItem('token');
      queryClient.clear();
    },
  });

  const login = async (email: string, password: string) => {
    await loginMutation.mutateAsync({ email, password });
  };

  const loginWithGoogle = async (): Promise<void> => {
    window.location.href = `${Config.API_AUTH_URL}/google`;
  };

  const logout = async (token: string) => {
    await logoutMutation.mutateAsync(token);
  };

  return (
    <AuthContext.Provider value={{ login, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};