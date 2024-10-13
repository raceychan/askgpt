import React, { createContext, useContext } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Config } from "@/config/config";
import { useNavigate } from "@tanstack/react-router";
import { AxiosError } from "axios";
import { useState } from "react";

import {
  AuthService,
  UserService,
  PublicUserInfo,
  LoginError,
  LoginResponse,
} from "@/lib/api";

interface AuthContextType {
  loginMutation: ReturnType<typeof useMutation>;
  login: (email: string, password: string) => void;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  signup: (email: string, password: string, userName?: string) => void;
  user: PublicUserInfo;
  isLoading: boolean;
}
const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const signup = async (email: string, password: string, userName?: string) => {
    const resp = await AuthService.signup({
      body: { user_name: userName, email: email, password: password },
    });

    if (resp.data) {
      console.log(resp.data);
      navigate({ to: "/login" }); // Redirect after successful signup
    } else {
      setError("Signup failed: " + (resp.error as AxiosError).message);
      throw resp.error;
    }
  };

  const { data: user, isLoading } = useQuery<PublicUserInfo, Error>({
    queryKey: ["user"],
    queryFn: async () => {
      const response = await UserService.getPublicUser();
      if (!response.data) {
        throw new Error(`Failed to get public user: ${response.error}`);
      }
      return response.data;
    },
    enabled: isLoggedIn(),
  }) as { data: PublicUserInfo; isLoading: boolean };

  const login = async (email: string, password: string) => {
    const response = await AuthService.login({
      body: { username: email, password: password },
    });
    if (!response.data) {
      throw Error(`Failed to login ${response.error}`);
    }
    const token = response.data;
    localStorage.setItem("access_token", token.access_token);
  };

  const loginMutation = useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      login(credentials.email, credentials.password),
    onSuccess: () => {
      navigate({ to: "/" });
    },
    onError: (error: LoginError) => {
      let errDetail = error.detail as any;

      if (error instanceof AxiosError) {
        errDetail = error.message;
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong";
      }

      setError(errDetail);
    },
  });

  const loginWithGoogle = async (): Promise<void> => {
    window.location.href = `${Config.API_AUTH_URL}/google`;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    navigate({ to: "/login" });
  };

  return (
    <AuthContext.Provider
      value={{
        loginMutation,
        // login,
        loginWithGoogle,
        logout,
        signup,
        user,
        isLoading,
      }}
    >
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

export { isLoggedIn };
export default useAuth;
