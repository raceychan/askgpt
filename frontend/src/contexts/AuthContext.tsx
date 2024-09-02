import React, { createContext, useContext } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Config } from "@/config/config";

import { AuthService, AuthLoginError } from "@/lib/api";

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

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();

  const login = async (email: string, password: string) => {
    await loginMutation.mutateAsync({ email, password });
  };

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
      localStorage.setItem("token", access_token);
    },
    onError: (error: unknown) => {
      console.error("Login failed:", error);
      let errorMessage = "An error occurred during login. Please try again.";
      // if (axios.isAxiosError(error) && error.response) {
      //   errorMessage = error.response.data.message || errorMessage;
      // }
      throw error;
    },
  });

  const loginWithGoogle = async (): Promise<void> => {
    window.location.href = `${Config.API_AUTH_URL}/google`;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
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
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
